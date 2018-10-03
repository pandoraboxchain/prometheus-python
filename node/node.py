import asyncio
import os

from chain.dag import Dag
from chain.epoch import Epoch
from chain.signed_block import SignedBlock
from chain.block_factory import BlockFactory
from chain.params import Round, Duration, MINIMAL_SECRET_SHARERS, TOTAL_SECRET_SHARERS
from chain.merger import Merger
from node.behaviour import Behaviour
from node.block_signers import BlockSigner
from node.permissions import Permissions
from node.validators import Validators
from tools.time import Time
from transaction.gossip_transaction import NegativeGossipTransaction, PositiveGossipTransaction
from transaction.mempool import Mempool
from transaction.transaction_parser import TransactionParser
from transaction.secret_sharing_transactions import PublicKeyTransaction, PrivateKeyTransaction, SplitRandomTransaction
from transaction.stake_transaction import StakeHoldTransaction, StakeReleaseTransaction,  PenaltyTransaction
from transaction.commit_transactions import CommitRandomTransaction, RevealRandomTransaction
from verification.transaction_verifier import TransactionVerifier
from verification.block_verifier import BlockVerifier 
from crypto.keys import Keys
from crypto.private import Private
from crypto.secret import split_secret, encode_splits


class DummyLogger(object):
    def __getattr__(self, name):
        return lambda *x: None


class Node:
    
    def __init__(self, genesis_creation_time, node_id, network,
                 block_signer=BlockSigner(Private.generate()),
                 validators=Validators(),
                 behaviour=Behaviour(),
                 logger=DummyLogger()):
        self.logger = logger
        self.dag = Dag(genesis_creation_time)
        self.epoch = Epoch(self.dag)
        self.epoch.set_logger(self.logger)
        self.dag.subscribe_to_new_block_notification(self.epoch)
        self.permissions = Permissions(self.epoch, validators)
        self.mempool = Mempool()
        self.behaviour = behaviour

        self.block_signer = block_signer
        self.logger.info("Public key is %s", Keys.to_visual_string(Private.publickey(block_signer.private_key)))
        self.network = network
        self.node_id = node_id
        self.epoch_private_keys = []  # TODO make this single element
        # self.epoch_private_keys where first element is era number, and second is key to reveal commited random
        self.reveals_to_send = {}
        self.sent_shares_epochs = []  # epoch hashes of secret shares
        self.last_expected_timeslot = 0

    def start(self):
        pass

    def handle_timeslot_changed(self, previous_timeslot_number, current_timeslot_number):
        self.last_expected_timeslot = current_timeslot_number
        if previous_timeslot_number not in self.dag.blocks_by_number:
            # get all tops and hashes for sending negative gossip
            for previous_hash in self.dag.get_top_blocks_hashes():
                self.broadcast_gossip_negative(previous_timeslot_number, previous_hash)
            return True
        return False

    def step(self):
        current_block_number = self.epoch.get_current_timeframe_block_number()

        if self.epoch.is_new_epoch_upcoming(current_block_number):
            self.epoch.accept_tops_as_epoch_hashes()

        # service method for update node behavior (if behavior is temporary)
        self.behaviour.update(Epoch.get_epoch_number(current_block_number))

        current_round = self.epoch.get_round_by_block_number(current_block_number)
        if current_round == Round.PUBLIC:
            self.try_to_publish_public_key(current_block_number)
        elif current_round == Round.SECRETSHARE:
            self.try_to_share_random()
            # elif current_round == Round.PRIVATE:
            # do nothing as private key should be included to block by block signer
        elif current_round == Round.COMMIT:
            self.try_to_commit_random()
        elif current_round == Round.REVEAL:
            self.try_to_reveal_random()
        elif current_round == Round.FINAL:
            # at this point we may remove everything systemic from mempool,
            # so it does not interfere with pubkeys for next epoch
            self.mempool.remove_all_systemic_transactions()

        if self.behaviour.wants_to_hold_stake:
            self.broadcast_stakehold_transaction()
            self.behaviour.wants_to_hold_stake = False

        if self.behaviour.wants_to_release_stake:
            self.broadcast_stakerelease_transaction()
            self.behaviour.wants_to_release_stake = False

        if current_block_number != self.last_expected_timeslot:
            should_wait = self.handle_timeslot_changed(previous_timeslot_number=self.last_expected_timeslot,
                                                       current_timeslot_number=current_block_number)
            if should_wait:
                return
        self.try_to_sign_block(current_block_number)

    async def run(self):
        while True:
            self.step()
            await asyncio.sleep(1)
    
    def try_to_sign_block(self, current_block_number):        
        epoch_block_number = Epoch.convert_to_epoch_block_number(current_block_number)
        
        allowed_to_sign = False
        epoch_hashes = self.epoch.get_epoch_hashes()
        for top, epoch_hash in epoch_hashes.items():
            permission = self.permissions.get_sign_permission(epoch_hash, epoch_block_number)
            if permission.public_key == Private.publickey(self.block_signer.private_key):
                allowed_to_sign = True
                break

        block_has_not_been_signed_yet = not self.epoch.is_current_timeframe_block_present()
        if allowed_to_sign and block_has_not_been_signed_yet:
            should_skip_maliciously = self.behaviour.is_malicious_skip_block()
            # first_epoch_ever = self.epoch.get_epoch_number(current_block_number) == 1
            if should_skip_maliciously:  # and not first_epoch_ever: # skip first epoch check
                self.epoch_private_keys.clear()
                self.logger.info("Maliciously skiped block")
            else:
                self.sign_block(current_block_number)

    def sign_block(self, current_block_number):
        current_round_type = self.epoch.get_round_by_block_number(current_block_number)
        
        transactions = self.mempool.pop_round_system_transactions(current_round_type)

        merger = Merger(self.dag)
        top, conflicts = merger.get_top_and_conflicts()
        
        if current_round_type == Round.PRIVATE:
            if self.epoch_private_keys:
                key_reveal_tx = self.form_private_key_reveal_transaction()
                transactions.append(key_reveal_tx)

        if conflicts:
            penalty = self.form_penalize_violators_transaction(conflicts)
            transactions.append(penalty)

        current_top_blocks = [top]
        if conflicts:
            current_top_blocks += conflicts
        
        block = BlockFactory.create_block_dummy(current_top_blocks)
        block.system_txs = transactions
        signed_block = BlockFactory.sign_block(block, self.block_signer.private_key)
        self.dag.add_signed_block(current_block_number, signed_block)
        if not self.behaviour.transport_cancel_block_broadcast:  # behaviour flag for cancel block broadcast
            self.logger.debug("Broadcasting signed block number %s", current_block_number)
            self.network.broadcast_block(self.node_id, signed_block.pack())
        else:
            self.logger.info("Created but maliciously skipped broadcasted block")

        if self.behaviour.is_malicious_excessive_block():
            additional_block_timestamp = block.timestamp + 1
            block = BlockFactory.create_block_with_timestamp(current_top_blocks, additional_block_timestamp)
            block.system_txs = transactions.copy()
            signed_block = BlockFactory.sign_block(block, self.block_signer.private_key)
            self.dag.add_signed_block(current_block_number, signed_block)
            self.logger.info("Sending additional block")
            self.network.broadcast_block(self.node_id, signed_block.pack())

    def try_to_publish_public_key(self, current_block_number):
        if self.epoch_private_keys:
            return
            
        node_pubkey = Private.publickey(self.block_signer.private_key)
        
        pubkey_publishers = []
        for _, epoch_hash in self.epoch.get_epoch_hashes().items():
            pubkey_publishers += self.permissions.get_ordered_randomizers_pubkeys_for_round(epoch_hash, Round.PUBLIC)

        for publisher in pubkey_publishers:
            if node_pubkey == publisher.public_key:
                node_private = self.block_signer.private_key
                generated_private = Private.generate()
                tx = PublicKeyTransaction()
                tx.generated_pubkey = Private.publickey(generated_private)
                tx.pubkey = Private.publickey(node_private)
                tx.signature = Private.sign(tx.get_hash(), node_private)
                if self.behaviour.malicious_wrong_signature:
                    tx.signature += 1
                    
                self.epoch_private_keys.append(generated_private)
                self.logger.debug("Broadcasted public key")
                self.logger.debug(Keys.to_visual_string(tx.generated_pubkey))
                self.mempool.add_transaction(tx)
                self.network.broadcast_transaction(self.node_id, TransactionParser.pack(tx))
    
    def try_to_share_random(self):
        pubkey = Private.publickey(self.block_signer.private_key)
        epoch_hashes = self.epoch.get_epoch_hashes()
        for top, epoch_hash in epoch_hashes.items():
            if epoch_hash in self.sent_shares_epochs: continue
            allowed_to_share_random = self.permissions.get_secret_sharers_pubkeys(epoch_hash)
            if not pubkey in allowed_to_share_random: continue
            split_random = self.form_split_random_transaction(top, epoch_hash)
            self.sent_shares_epochs.append(epoch_hash)
            self.mempool.add_transaction(split_random)
            self.network.broadcast_transaction(self.node_id, TransactionParser.pack(split_random))

    def try_to_commit_random(self):
        pubkey = Private.publickey(self.block_signer.private_key)
        epoch_hashes = self.epoch.get_epoch_hashes().values()
        for epoch_hash in epoch_hashes:
            if not epoch_hash in self.reveals_to_send:
                allowed_to_commit_list = self.permissions.get_commiters_pubkeys(epoch_hash)
                if not pubkey in allowed_to_commit_list: continue
                commit, reveal = self.create_commit_reveal_pair(self.block_signer.private_key, os.urandom(32), epoch_hash)
                self.reveals_to_send[epoch_hash] = reveal
                self.logger.info("Broadcasting commit")
                self.mempool.add_transaction(commit)
                self.network.broadcast_transaction(self.node_id, TransactionParser.pack(commit))
    
    def try_to_reveal_random(self):
        for epoch_hash in list(self.reveals_to_send.keys()):
            reveal = self.reveals_to_send[epoch_hash]
            self.logger.info("Broadcasting reveal")
            self.mempool.add_transaction(reveal)
            self.network.broadcast_transaction(self.node_id, TransactionParser.pack(reveal))
            del self.reveals_to_send[epoch_hash]

    def form_private_key_reveal_transaction(self):
        tx = PrivateKeyTransaction()
        tx.key = Keys.to_bytes(self.epoch_private_keys.pop(0))
        return tx

    def form_penalize_violators_transaction(self, conflicts):
        for conflict in conflicts:
            block = self.dag.blocks_by_hash[conflict]
            self.network.broadcast_block_out_of_timeslot(self.node_id, block.pack())
        
        self.logger.info("Forming transaction with conflicting blocks")
        self.logger.info(conflict.hex())

        penalty = PenaltyTransaction()
        penalty.conflicts = conflicts
        penalty.signature = Private.sign(penalty.get_hash(), self.block_signer.private_key)
        return penalty

    def form_split_random_transaction(self, top_hash, epoch_hash):
        ordered_senders = self.permissions.get_ordered_randomizers_pubkeys_for_round(epoch_hash, Round.PUBLIC)
        published_pubkeys = self.epoch.get_public_keys_for_epoch(top_hash)
        
        self.logger.info("Ordered pubkeys for secret sharing:")
        sorted_published_pubkeys = []
        for sender in ordered_senders:
            raw_pubkey = Keys.to_bytes(sender.public_key)
            if raw_pubkey in published_pubkeys: 
                generated_pubkey = published_pubkeys[raw_pubkey]
                sorted_published_pubkeys.append(Keys.from_bytes(generated_pubkey))
                self.logger.info(Keys.to_visual_string(generated_pubkey))
            else:
                sorted_published_pubkeys.append(None)
                self.logger.info("None")

        tx = self.form_secret_sharing_transaction(sorted_published_pubkeys, epoch_hash)
        return tx

    def form_secret_sharing_transaction(self, sorted_public_keys, epoch_hash):
        random_bytes = os.urandom(32)
        splits = split_secret(random_bytes, MINIMAL_SECRET_SHARERS, TOTAL_SECRET_SHARERS)
        encoded_splits = encode_splits(splits, sorted_public_keys)
        self.logger.info("Formed split random")
        
        tx = SplitRandomTransaction()
        tx.pieces = encoded_splits
        tx.signature = Private.sign(tx.get_signing_hash(epoch_hash), self.block_signer.private_key)
        return tx

    def get_allowed_signers_for_next_block(self, block):
        current_block_number = self.epoch.get_current_timeframe_block_number()
        epoch_block_number = Epoch.convert_to_epoch_block_number(current_block_number)
        if self.epoch.is_new_epoch_upcoming(current_block_number):
            self.epoch.accept_tops_as_epoch_hashes()
        epoch_hashes = self.epoch.get_epoch_hashes()
        allowed_signers = []
        for prev_hash in block.prev_hashes:
            epoch_hash = None
            if prev_hash in epoch_hashes:
                epoch_hash = epoch_hashes[prev_hash]
            else:
                epoch_hash = self.epoch.find_epoch_hash_for_block(prev_hash)
            
            if epoch_hash:
                # self.logger.info("Calculating permissions from epoch_hash %s", epoch_hash.hex())
                allowed_pubkey = self.permissions.get_sign_permission(epoch_hash, epoch_block_number)
                allowed_signers.append(allowed_pubkey)

        assert len(allowed_signers) > 0, "No signers allowed to sign next block"
        return allowed_signers

    # -------------------------------------------------------------------------------
    # Handlers
    # -------------------------------------------------------------------------------
    def handle_block_message(self, node_id, raw_signed_block):

        signed_block = SignedBlock()
        signed_block.parse(raw_signed_block)
        
        allowed_signers = self.get_allowed_signers_for_next_block(signed_block.block)

        is_block_allowed = False
        for allowed_signer in allowed_signers:
            if signed_block.verify_signature(allowed_signer.public_key):
                is_block_allowed = True
                break
        
        if is_block_allowed:
            block = signed_block.block
            block_verifier = BlockVerifier(self.epoch, self.logger)
            if block_verifier.check_if_valid(block):
                current_block_number = self.epoch.get_current_timeframe_block_number()
                self.dag.add_signed_block(current_block_number, signed_block)
                self.mempool.remove_transactions(block.system_txs)
            else:
                self.logger.error("Block was not added. Considered invalid")
        else:
            self.logger.error("Received block from %d, but it's signature is wrong", node_id)

    def handle_block_out_of_timeslot(self, node_id, raw_signed_block):
        signed_block = SignedBlock()
        signed_block.parse(raw_signed_block)

        block_hash = signed_block.get_hash()
        if block_hash in self.dag.blocks_by_hash:
            self.logger.info("Received conflicting block, but it already exists in DAG")
            return

        block_number = self.epoch.get_block_number_from_timestamp(signed_block.block.timestamp)

        allowed_signers = self.get_allowed_signers_for_block_number(block_number)
        is_block_allowed = False
        for allowed_signer in allowed_signers:
            if signed_block.verify_signature(allowed_signer):
                is_block_allowed = True
                break

        if is_block_allowed:
            block = signed_block.block
            block_verifier = BlockVerifier(self.epoch, self.logger)
            if block_verifier.check_if_valid(block):
                self.dag.add_signed_block(block_number, signed_block)
                self.mempool.remove_transactions(signed_block.block.system_txs)
                self.logger.error("Added block out of timeslot")
            else:
                self.logger.error("Block was not added. Considered invalid")
        else:
            self.logger.error("Received block from %d, but it's signature is wrong", node_id)

    def handle_transaction_message(self, node_id, raw_transaction):
        transaction = TransactionParser.parse(raw_transaction)
        current_block_number = self.epoch.get_current_timeframe_block_number()
        is_new_epoch_upcoming = self.epoch.is_new_epoch_upcoming(current_block_number)

        #switch no new epoch if necessary
        if is_new_epoch_upcoming:
            self.epoch.accept_tops_as_epoch_hashes()

        epoch_block_number = self.epoch.convert_to_epoch_block_number(current_block_number)
        verifier = TransactionVerifier(self.epoch, self.permissions, epoch_block_number, self.logger)
        # print("Node ", self.node_id, "received transaction with hash",
        # transaction.get_hash().hexdigest(), " from node ", node_id)
        if verifier.check_if_valid(transaction):
            # print("It is valid. Adding to mempool")
            self.mempool.add_transaction(transaction)
        else:
            self.logger.error("Received tx is invalid")

    def handle_gossip_negative(self, node_id, raw_gossip):
        transaction = TransactionParser.parse(raw_gossip)
        current_block_number = self.epoch.get_current_timeframe_block_number()
        epoch_block_number = self.epoch.convert_to_epoch_block_number(current_block_number)
        verifier = TransactionVerifier(self.epoch, self.permissions, epoch_block_number, self.logger)
        if verifier.check_if_valid(transaction):
            self.mempool.add_transaction(transaction)
            if self.dag.has_block_number(transaction.number_of_block):
                signed_block_by_number = self.dag.blocks_by_number[transaction.number_of_block]
                self.broadcast_gossip_positive(signed_block_by_number[0].get_hash())
                self.logger.error("Received valid gossip negative. Requested block %i found",
                                  transaction.number_of_block)
            else:
                # received gossip block but not have requested block for gossip positive broadcasting
                self.logger.error("Received valid gossip negative. Requested block %i not found",
                                  transaction.number_of_block)
        else:
            self.logger.error("Received gossip negative tx is invalid")

    def handle_gossip_positive(self, node_id, raw_gossip):
        transaction = TransactionParser.parse(raw_gossip)
        current_block_number = self.epoch.get_current_timeframe_block_number()
        epoch_block_number = self.epoch.convert_to_epoch_block_number(current_block_number)
        verifier = TransactionVerifier(self.epoch, self.permissions, epoch_block_number, self.logger)
        if verifier.check_if_valid(transaction):
            self.mempool.add_transaction(transaction)  # is need to add tx to self.mempool() ---> ?
            if transaction.block_hash not in self.dag.blocks_by_hash:  # ----> !!! make request ONLY if block
                                                                            # in timeslot (and may be by anchor hash)
                self.network.get_block_by_hash(receiver_node_id=node_id,  # request TO ----> receiver_node_id
                                               block_hash=transaction.block_hash)
        else:
            self.logger.error("Received gossip positive tx is invalid")

    # -------------------------------------------------------------------------------
    # Broadcast
    # -------------------------------------------------------------------------------
    def broadcast_stakehold_transaction(self):
        tx = StakeHoldTransaction()
        tx.amount = 1000
        node_private = self.block_signer.private_key
        tx.pubkey = Private.publickey(node_private)
        tx.signature = Private.sign(tx.get_hash(), node_private)
        self.logger.info("Broadcasted StakeHold transaction")
        self.network.broadcast_transaction(self.node_id, TransactionParser.pack(tx))

    def broadcast_stakerelease_transaction(self):
        tx = StakeReleaseTransaction()
        node_private = self.block_signer.private_key
        tx.pubkey = Private.publickey(node_private)
        tx.signature = Private.sign(tx.get_hash(), node_private)
        self.logger.info("Broadcasted release stake transaction")
        self.network.broadcast_transaction(self.node_id, TransactionParser.pack(tx))

    def broadcast_gossip_negative(self, block_number, previous_block_hash):
        tx = NegativeGossipTransaction()
        node_private = self.block_signer.private_key
        tx.pubkey = Private.publickey(node_private)
        tx.timestamp = Time.get_current_time()
        tx.number_of_block = block_number
        tx.anchor_block_hash = previous_block_hash
        tx.signature = Private.sign(tx.get_hash(), node_private)
        self.logger.info("Broadcasted negative gossip transaction")
        self.network.broadcast_gossip_negative(self.node_id, TransactionParser.pack(tx))

    def broadcast_gossip_positive(self, signed_block_hash):
        tx = PositiveGossipTransaction()
        node_private = self.block_signer.private_key
        tx.pubkey = Private.publickey(node_private)
        tx.timestamp = Time.get_current_time()
        tx.block_hash = signed_block_hash
        tx.signature = Private.sign(tx.get_hash(), node_private)
        self.logger.info("Broadcasted positive gossip transaction")
        self.network.broadcast_gossip_positive(self.node_id, TransactionParser.pack(tx))

    # -------------------------------------------------------------------------------
    # Targeted request
    # -------------------------------------------------------------------------------
    def request_block_by_hash(self, block_hash):
        # no need validate/ public info ?
        signed_block = self.dag.blocks_by_hash[block_hash]
        self.network.broadcast_block_out_of_timeslot(self.node_id, signed_block.pack())

    # -------------------------------------------------------------------------------
    # Internal
    # -------------------------------------------------------------------------------
    @staticmethod
    def create_commit_reveal_pair(node_private, random_bytes, epoch_hash):
        private = Private.generate()
        public = Private.publickey(node_private)
        encoded = Private.encrypt(random_bytes, private)

        commit = CommitRandomTransaction()
        commit.rand = encoded
        commit.pubkey = Keys.to_bytes(public)
        commit.signature = Private.sign(commit.get_signing_hash(epoch_hash), node_private)

        reveal = RevealRandomTransaction()
        reveal.commit_hash = commit.get_hash()
        reveal.key = Keys.to_bytes(private)

        return commit, reveal

    def get_allowed_signers_for_block_number(self, block_number):
        prev_epoch_number = self.epoch.get_epoch_number(block_number) - 1
        prev_epoch_start = self.epoch.get_epoch_start_block_number(prev_epoch_number)
        prev_epoch_end = self.epoch.get_epoch_end_block_number(prev_epoch_number)
        
        # this will extract every unconnected block in epoch, which is practically epoch hash
        # TODO maybe consider blocks to be epoch hashes if they are in final round and consider everything else is orphan
        epoch_hashes = self.dag.get_branches_for_timeslot_range(prev_epoch_start, prev_epoch_end)
        
        if prev_epoch_number == 0:
            epoch_hashes = [self.dag.genesis_block().get_hash()]

        allowed_signers = []
        for epoch_hash in epoch_hashes:
            epoch_block_number = Epoch.convert_to_epoch_block_number(block_number)
            allowed_pubkey = self.permissions.get_sign_permission(epoch_hash, epoch_block_number).public_key
            allowed_signers.append(allowed_pubkey)

        assert len(allowed_signers) > 0, "No signers allowed to sign block"
        return allowed_signers

