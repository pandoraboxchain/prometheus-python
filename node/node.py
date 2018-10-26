import asyncio
import os

from chain.dag import Dag
from chain.epoch import Epoch
from chain.signed_block import SignedBlock
from chain.block_factory import BlockFactory
from chain.params import Round, MINIMAL_SECRET_SHARERS, TOTAL_SECRET_SHARERS, ZETA
from chain.transaction_factory import TransactionFactory
from chain.conflict_finder import ConflictFinder
from chain.conflict_watcher import ConflictWatcher
from node.behaviour import Behaviour
from node.block_signers import BlockSigner
from node.permissions import Permissions
from node.validators import Validators
from transaction.utxo import Utxo
from transaction.mempool import Mempool
from transaction.transaction_parser import TransactionParser
from transaction.payment_transaction import PaymentTransaction
from verification.in_block_transactions_acceptor import InBlockTransactionsAcceptor
from verification.mempool_transactions_acceptor import MempoolTransactionsAcceptor
from verification.block_acceptor import BlockAcceptor
from crypto.keys import Keys
from crypto.private import Private
from crypto.secret import split_secret, encode_splits
from hashlib import sha256



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
        self.permissions = Permissions(self.epoch, validators)
        self.mempool = Mempool()
        self.utxo = Utxo(self.logger)
        self.conflict_watcher = ConflictWatcher(self.dag)
        self.behaviour = behaviour

        self.block_signer = block_signer
        self.node_pubkey = Private.publickey(block_signer.private_key)
        self.logger.info("Public key is %s", Keys.to_visual_string(self.node_pubkey))
        self.network = network
        self.node_id = node_id
        self.epoch_private_keys = []  # TODO make this single element
        # self.epoch_private_keys where first element is era number, and second is key to reveal commited random
        self.reveals_to_send = {}
        self.sent_shares_epochs = []  # epoch hashes of secret shares
        self.last_expected_timeslot = 0
        self.last_signed_block_number = 0
        self.tried_to_sign_current_block = False
        self.owned_utxos = []

    def start(self):
        pass

    def handle_timeslot_changed(self, previous_timeslot_number, current_timeslot_number):
        self.last_expected_timeslot = current_timeslot_number
        if previous_timeslot_number not in self.dag.blocks_by_number:
            negative_by_block = self.mempool.get_negative_gossips_by_block(previous_timeslot_number)
            if len(negative_by_block) < ZETA:  # validate count of negative gossip by block
                self.broadcast_gossip_negative(previous_timeslot_number)
            # even if do not broadcast negative gossip perform wait by one step
            return True
        return False

    def step(self):
        current_block_number = self.epoch.get_current_timeframe_block_number()

        if self.epoch.is_new_epoch_upcoming(current_block_number):
            self.epoch.accept_tops_as_epoch_hashes()

        # service method for update node behavior (if behavior is temporary)
        self.behaviour.update(Epoch.get_epoch_number(current_block_number))
        # service method for update transport behavior (if behavior is temporary)
        self.behaviour.update_transport(current_block_number)

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

        if self.behaviour.malicious_send_negative_gossip_count > 0:
            self.broadcast_gossip_negative(self.last_expected_timeslot)
            self.behaviour.malicious_send_negative_gossip_count -= 1
        if self.behaviour.malicious_send_positive_gossip_count > 0:
            zero_block = self.dag.blocks_by_number[0][0].block  # send genesis block malicious
            self.broadcast_gossip_positive(zero_block.get_hash())
            self.behaviour.malicious_send_positive_gossip_count -= 1

        if self.owned_utxos:
            self.broadcast_payments()

        if current_block_number != self.last_expected_timeslot:
            self.tried_to_sign_current_block = False
            should_wait = self.handle_timeslot_changed(previous_timeslot_number=self.last_expected_timeslot,
                                                       current_timeslot_number=current_block_number)
            if should_wait:
                return
        if not self.tried_to_sign_current_block:
            self.try_to_sign_block(current_block_number)
            self.tried_to_sign_current_block = True  # will reset in next timeslot

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
            if permission.public_key == self.node_pubkey:
                allowed_to_sign = True
                break

        if allowed_to_sign:
            should_skip_maliciously = self.behaviour.is_malicious_skip_block()
            # first_epoch_ever = self.epoch.get_epoch_number(current_block_number) == 1
            if should_skip_maliciously:  # and not first_epoch_ever: # skip first epoch check
                self.epoch_private_keys.clear()
                self.logger.info("Maliciously skiped block")
            else:
                if self.last_signed_block_number < current_block_number:
                    self.last_signed_block_number = current_block_number
                    self.sign_block(current_block_number)
                else:
                    # skip once more block broadcast in same timeslot
                    pass

    def sign_block(self, current_block_number):
        current_round_type = self.epoch.get_round_by_block_number(current_block_number)
        
        system_txs = self.get_system_transactions_for_signing(current_round_type)
        payment_txs = self.get_payment_transactions_for_signing(current_block_number)

        tops = self.dag.get_top_blocks_hashes()
        chosen_top = self.dag.get_longest_chain_top(tops)
        conflicting_tops = [top for top in tops if top != chosen_top]
        
        current_top_blocks = [chosen_top] + conflicting_tops #first link in dag is not considered conflict, the rest is.
        
        block = BlockFactory.create_block_dummy(current_top_blocks)
        block.system_txs = system_txs
        block.payment_txs = payment_txs
        signed_block = BlockFactory.sign_block(block, self.block_signer.private_key)
        self.dag.add_signed_block(current_block_number, signed_block)
        self.utxo.apply_payments(payment_txs)
        if not self.behaviour.transport_cancel_block_broadcast:  # behaviour flag for cancel block broadcast
            self.logger.debug("Broadcasting signed block number %s", current_block_number)
            self.network.broadcast_block(self.node_id, signed_block.pack())
        else:
            self.logger.info("Created but maliciously skipped broadcasted block")

        if self.behaviour.is_malicious_excessive_block():
            additional_block_timestamp = block.timestamp + 1
            additional_block = BlockFactory.create_block_with_timestamp(current_top_blocks, additional_block_timestamp)
            additional_block.system_txs = block.system_txs
            additional_block.payment_txs = block.payment_txs
            signed_add_block = BlockFactory.sign_block(additional_block, self.block_signer.private_key)
            self.dag.add_signed_block(current_block_number, signed_add_block)
            self.logger.info("Sending additional block")
            self.network.broadcast_block(self.node_id, signed_add_block.pack())

    def get_system_transactions_for_signing(self, round):
        system_txs = self.mempool.pop_round_system_transactions(round)

        # skip non valid system_txs
        verifier = InBlockTransactionsAcceptor(self.epoch, self.permissions, self.logger)
        system_txs = [t for t in system_txs if verifier.check_if_valid(t)]
        # get gossip conflicts hashes (validate_gossip() ---> [gossip_negative_hash, gossip_positive_hash])
        conflicts_gossip = self.validate_gossip(self.dag, self.mempool)
        gossip_mempool_txs = self.mempool.pop_current_gossips()  # POP gossips to block
        system_txs += gossip_mempool_txs

        if round == Round.PRIVATE:
            if self.epoch_private_keys:
                key_reveal_tx = self.form_private_key_reveal_transaction()
                system_txs.append(key_reveal_tx)

        if conflicts_gossip:
            for conflict in conflicts_gossip:
                penalty_gossip_tx = \
                    TransactionFactory.create_penalty_gossip_transaction(conflict=conflict,
                                                                         node_private=self.block_signer.private_key)
                system_txs.append(penalty_gossip_tx)
        
        return system_txs

    def get_payment_transactions_for_signing(self, block_number):
        node_public = Private.publickey(self.block_signer.private_key)
        pseudo_address = sha256(node_public).digest()
        block_reward = TransactionFactory.create_block_reward(pseudo_address, block_number)
        block_reward_hash = block_reward.get_hash()
        self.owned_utxos.append(block_reward_hash)
        payment_txs = [block_reward] + self.mempool.pop_payment_transactions()
        return payment_txs

    def try_to_publish_public_key(self, current_block_number):
        if self.epoch_private_keys:
            return
        
        epoch_hashes = self.epoch.get_epoch_hashes()
        for _, epoch_hash in epoch_hashes.items():
            allowed_round_validators = self.permissions.get_ordered_randomizers_pubkeys_for_round(epoch_hash, Round.PUBLIC)
            pubkey_publishers_pubkeys = [validator.public_key for validator in allowed_round_validators]
            if self.node_pubkey in pubkey_publishers_pubkeys:
                node_private = self.block_signer.private_key
                pubkey_index = self.permissions.get_signer_index_from_public_key(self.node_pubkey, epoch_hash)

                generated_private = Private.generate()
                tx = TransactionFactory.create_public_key_transaction(generated_private=generated_private,
                                                                      epoch_hash=epoch_hash,
                                                                      validator_index=pubkey_index,
                                                                      node_private=node_private)
                if self.behaviour.malicious_wrong_signature:
                    tx.signature = b'0' + tx.signature[1:]
                    
                self.epoch_private_keys.append(generated_private)
                self.logger.debug("Broadcasted public key")
                self.logger.debug(Keys.to_visual_string(tx.generated_pubkey))
                self.mempool.add_transaction(tx)
                self.network.broadcast_transaction(self.node_id, TransactionParser.pack(tx))
    
    def try_to_share_random(self):
        epoch_hashes = self.epoch.get_epoch_hashes()
        for top, epoch_hash in epoch_hashes.items():
            if epoch_hash in self.sent_shares_epochs: continue
            allowed_to_share_random = self.permissions.get_secret_sharers_pubkeys(epoch_hash)
            if not self.node_pubkey in allowed_to_share_random: continue
            split_random = self.form_split_random_transaction(top, epoch_hash)
            self.sent_shares_epochs.append(epoch_hash)
            self.mempool.add_transaction(split_random)
            self.network.broadcast_transaction(self.node_id, TransactionParser.pack(split_random))

    def try_to_commit_random(self):
        epoch_hashes = self.epoch.get_epoch_hashes().values()
        for epoch_hash in epoch_hashes:
            if epoch_hash not in self.reveals_to_send:
                allowed_to_commit_list = self.permissions.get_commiters_pubkeys(epoch_hash)
                if self.node_pubkey not in allowed_to_commit_list:
                    continue
                pubkey_index = self.permissions.get_committer_index_from_public_key(self.node_pubkey, epoch_hash)
                commit, reveal = TransactionFactory.create_commit_reveal_pair(self.block_signer.private_key, os.urandom(32), pubkey_index, epoch_hash)
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
        tx = TransactionFactory.create_private_key_transaction(self.epoch_private_keys.pop(0))
        return tx

    def form_penalize_violators_transaction(self, conflicts):
        for conflict in conflicts:
            block = self.dag.blocks_by_hash[conflict]
            self.network.broadcast_block_out_of_timeslot(self.node_id, block.pack())
        
        self.logger.info("Forming transaction with conflicting blocks")
        self.logger.info(conflict.hex())
        node_private = self.block_signer.private_key

        tx = TransactionFactory.create_penalty_transaction(conflicts, node_private)
        return tx

    def form_split_random_transaction(self, top_hash, epoch_hash):
        ordered_senders = self.permissions.get_ordered_randomizers_pubkeys_for_round(epoch_hash, Round.PUBLIC)
        published_pubkeys = self.epoch.get_public_keys_for_epoch(top_hash)
        
        self.logger.info("Ordered pubkeys for secret sharing:")
        sorted_published_pubkeys = []
        for sender in ordered_senders:
            raw_pubkey = Keys.to_bytes(sender.public_key)
            raw_pubkey_index = self.permissions.get_signer_index_from_public_key(raw_pubkey, epoch_hash)
            if raw_pubkey_index in published_pubkeys:
                generated_pubkey = published_pubkeys[raw_pubkey_index]
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

        node_private = self.block_signer.private_key
        pubkey_index = self.permissions.get_secret_sharer_from_public_key(self.node_pubkey, epoch_hash)

        tx = TransactionFactory.create_split_random_transaction(encoded_splits, pubkey_index, epoch_hash, node_private)
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
            block_verifier = BlockAcceptor(self.epoch, self.logger)
            if block_verifier.check_if_valid(block):
                current_block_number = self.epoch.get_current_timeframe_block_number()
                # проверять елси предок у данного блока в локальном даг
                #
                self.dag.add_signed_block(current_block_number, signed_block)
                self.mempool.remove_transactions(block.system_txs)
                self.mempool.remove_transactions(block.payment_txs)
                self.utxo.apply_payments(block.payment_txs)
            else:
                self.logger.error("Block was not added. Considered invalid")
        else:
            self.logger.error("Received block from %d, but its signature is wrong", node_id)

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
            block_verifier = BlockAcceptor(self.epoch, self.logger)
            if block_verifier.check_if_valid(block):
                self.dag.add_signed_block(block_number, signed_block)
                self.mempool.remove_transactions(block.system_txs)
                self.mempool.remove_transactions(block.payment_txs)
                self.utxo.apply_payments(block.payment_txs)
                self.logger.error("Added block out of timeslot")
            else:
                self.logger.error("Block was not added. Considered invalid")
        else:
            self.logger.error("Received block from %d, but it's signature is wrong", node_id)

    def handle_transaction_message(self, node_id, raw_transaction):
        transaction = TransactionParser.parse(raw_transaction)

        verifier = MempoolTransactionsAcceptor(self.epoch, self.permissions, self.logger)
        if verifier.check_if_valid(transaction):
            self.mempool.add_transaction(transaction)
        else:
            self.logger.error("Received tx is invalid")

    def handle_gossip_negative(self, node_id, raw_gossip):
        transaction = TransactionParser.parse(raw_gossip)
        verifier = MempoolTransactionsAcceptor(self.epoch, self.permissions, self.logger)
        if verifier.check_if_valid(transaction):
            self.mempool.append_gossip_tx(transaction)  # append negative gossip exclude duplicates
            current_gossips = self.mempool.get_negative_gossips_by_block(transaction.number_of_block)
            # check if current node send negative gossip ?
            for gossip in current_gossips:
                # negative gossip already send by node, skip positive gossip searching and broadcasting
                if gossip.pubkey == self.node_pubkey:
                    return

            if self.dag.has_block_number(transaction.number_of_block):
                signed_block_by_number = self.dag.blocks_by_number[transaction.number_of_block]
                self.broadcast_gossip_positive(signed_block_by_number[0].get_hash())
            else:
                # received gossip block but not have requested block for gossip positive broadcasting
                self.logger.error("Received valid gossip negative. Requested block %i not found",
                                  transaction.number_of_block)
        else:
            self.logger.error("Received gossip negative tx is invalid")

    def handle_gossip_positive(self, node_id, raw_gossip):
        transaction = TransactionParser.parse(raw_gossip)
        verifier = MempoolTransactionsAcceptor(self.epoch, self.permissions, self.logger)
        if verifier.check_if_valid(transaction):
            self.mempool.append_gossip_tx(transaction)
            if transaction.block_hash not in self.dag.blocks_by_hash:  # ----> ! make request ONLY if block in timeslot
                self.network.get_block_by_hash(sender_node_id=self.node_id,
                                               receiver_node_id=node_id,  # request TO ----> receiver_node_id
                                               block_hash=transaction.block_hash)
        else:
            self.logger.error("Received gossip positive tx is invalid")

    # -------------------------------------------------------------------------------
    # Broadcast
    # -------------------------------------------------------------------------------
    def broadcast_stakehold_transaction(self):
        node_private = self.block_signer.private_key
        tx = TransactionFactory.create_stake_hold_transaction(1000, node_private)
        self.logger.info("Broadcasted StakeHold transaction")
        self.network.broadcast_transaction(self.node_id, TransactionParser.pack(tx))

    def broadcast_stakerelease_transaction(self):
        node_private = self.block_signer.private_key
        tx = TransactionFactory.create_stake_release_transaction(node_private)
        self.logger.info("Broadcasted release stake transaction")
        self.network.broadcast_transaction(self.node_id, TransactionParser.pack(tx))

    def broadcast_gossip_negative(self, block_number):
        node_private = self.block_signer.private_key
        tx = TransactionFactory.create_negative_gossip_transaction(block_number, node_private)
        self.mempool.append_gossip_tx(tx)  # ADD ! TO LOCAL MEMPOOL BEFORE BROADCAST
        self.logger.info("Broadcasted negative gossip transaction")
        self.network.broadcast_gossip_negative(self.node_id, TransactionParser.pack(tx))

    def broadcast_gossip_positive(self, signed_block_hash):
        node_private = self.block_signer.private_key
        tx = TransactionFactory.create_positive_gossip_transaction(signed_block_hash, node_private)
        self.mempool.append_gossip_tx(tx)  # ADD ! TO LOCAL MEMPOOL BEFORE BROADCAST
        self.logger.info("Broadcasted positive gossip transaction")
        self.network.broadcast_gossip_positive(self.node_id, TransactionParser.pack(tx))

    def broadcast_payments(self):
        for utxo in self.owned_utxos:
            tx = TransactionFactory.create_payment(utxo, 0, [os.urandom(32), os.urandom(32)], [10, 5])
            self.mempool.add_transaction(tx)
            self.network.broadcast_transaction(self.node_id, TransactionParser.pack(tx))
            # self.logger.info("Broadcasted payment with hash %s", tx.get_hash())
        self.owned_utxos.clear()

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

    def get_allowed_signers_for_block_number(self, block_number):
        prev_epoch_number = self.epoch.get_epoch_number(block_number) - 1
        prev_epoch_start = self.epoch.get_epoch_start_block_number(prev_epoch_number)
        prev_epoch_end = self.epoch.get_epoch_end_block_number(prev_epoch_number)
        
        # this will extract every unconnected block in epoch, which is practically epoch hash
        # TODO maybe consider blocks to be epoch hashes if they are in final round and consider everything else is orphan
        epoch_hashes = self.dag.get_branches_for_timeslot_range(prev_epoch_start, prev_epoch_end + 1)
        
        if prev_epoch_number == 0:
            epoch_hashes = [self.dag.genesis_block().get_hash()]

        allowed_signers = []
        for epoch_hash in epoch_hashes:
            epoch_block_number = Epoch.convert_to_epoch_block_number(block_number)
            allowed_pubkey = self.permissions.get_sign_permission(epoch_hash, epoch_block_number).public_key
            allowed_signers.append(allowed_pubkey)

        assert len(allowed_signers) > 0, "No signers allowed to sign block"
        return allowed_signers

    @staticmethod
    def validate_gossip(dag, mempool):
        result = []

        # -------------- mempool validation
        mem_negative_gossips = mempool.get_all_negative_gossips()
        # for every negative in mempool get authors and positives
        for negative in mem_negative_gossips:  # we can have many negatives by not existing block
            negative_author = negative.pubkey
            # get block by negative number
            # skip another validations (if current validator have no block)
            if dag.has_block_number(negative.number_of_block):
                # get block hash
                blocks_by_negative = dag.blocks_by_number[negative.number_of_block]
                for block in blocks_by_negative:  # we can have more than one block by number
                    positives_for_negative = \
                        mempool.get_positive_gossips_by_block_hash(block.get_hash())
                    # if have no positives for negative - do nothing
                    for positive in positives_for_negative:
                        if positive.pubkey == negative_author:
                            # add to conflict result positive and negative gossips hash with same author
                            result.append([positive.get_hash(), negative.get_hash()])

        # -------------- dag validation
        # provide penalty for standalone positive gossip (without negative) ?
        # what else we can validate by tx_by_hash ?
        # dag_negative_gossips = dag.get_negative_gossips()
        # dag_positive_gossips = dag.get_positive_gossips()
        # dag_penalty_gossips = dag.get_penalty_gossips()
        return result


