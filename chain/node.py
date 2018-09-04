import time
import asyncio
import os
import logging

from base64 import b64decode,b64encode

from chain.node_api import NodeApi
from chain.dag import Dag
from chain.epoch import Round, Epoch
from chain.block_signer import BlockSigner
from chain.block_signers import BlockSigners
from chain.permissions import Permissions
from chain.signed_block import SignedBlock
from chain.block_factory import BlockFactory
from chain.params import Round, Duration
from chain.merger import Merger
from transaction.mempool import Mempool
from transaction.transaction import TransactionParser
from transaction.transaction import PublicKeyTransaction, PrivateKeyTransaction, SplitRandomTransaction
from transaction.stake_transaction import StakeHoldTransaction, StakeReleaseTransaction,  PenaltyTransaction
from transaction.transaction import CommitRandomTransaction, RevealRandomTransaction
from verification.transaction_verifier import TransactionVerifier
from verification.block_verifier import BlockVerifier
from crypto.enc_random import enc_part_random
from crypto.keys import Keys
from crypto.private import Private
from transaction.commits_set import CommitsSet
from crypto.secret import split_secret, encode_splits, decode_random
from gossip.gossip import NegativeGossip, PositiveGossip

class Node():
    
    def __init__(self, genesis_creation_time, node_id, network, logger, block_signer, behaviour):
        self.logger = logger
        self.dag = Dag(genesis_creation_time)
        self.epoch = Epoch(self.dag)
        self.epoch.set_logger(self.logger)
        self.dag.subscribe_to_new_block_notification(self.epoch)
        self.permissions = Permissions(self.epoch)
        self.mempool = Mempool()
        self.behaviour = behaviour

        if not block_signer:
            block_signer = BlockSigner()
            block_signer.set_private_key(Private.generate())

        self.block_signer = block_signer
        self.logger.info("Public key is %s", Keys.to_visual_string(block_signer.private_key.publickey()))
        self.network = network
        self.node_id = node_id
        self.epoch_private_keys = [] #TODO make this single element
        #self.epoch_private_keys where first element is era number, and second is key to reveal commited random
        self.reveals_to_send = {}
        self.sent_shares_epochs = [] #epoch hashes of secret shares 

    def start(self):
        pass

    async def run(self):
        while True:
            current_block_number = self.epoch.get_current_timeframe_block_number()
            if self.epoch.is_new_epoch_upcoming(current_block_number):
                self.epoch.accept_tops_as_epoch_hashes()
            
            self.behaviour.update(Epoch.get_epoch_number(current_block_number))
            current_round = self.epoch.get_round_by_block_number(current_block_number)
            if current_round == Round.PUBLIC:
                self.try_to_publish_public_key(current_block_number)
            elif current_round == Round.SECRETSHARE:
                self.try_to_share_random()
            elif current_round == Round.PRIVATE:
                #delete random if we published it in previous round
                #real private key publish will happen when signing block
                if hasattr(self, "self.last_epoch_random_published"):
                    del self.last_epoch_random_published
                #at this point we may remove everything systemic from mempool, so it does not interfere with pubkeys for next epoch
                self.mempool.remove_all_systemic_transactions()
            elif current_round == Round.COMMIT:
                self.try_to_commit_random()
            elif current_round == Round.REVEAL:
                self.try_to_reveal_random()
                              
            self.try_to_sign_block(current_block_number)

            if self.behaviour.wants_to_hold_stake:
                self.broadcast_stakehold_transaction()
                self.behaviour.wants_to_hold_stake = False
            
            if self.behaviour.wants_to_release_stake:
                self.broadcast_stakerelease_transaction()
                self.behaviour.wants_to_release_stake = False

            await asyncio.sleep(1)
    
    def try_to_sign_block(self, current_block_number):        
        epoch_block_number = Epoch.convert_to_epoch_block_number(current_block_number)
        
        allowed_to_sign = False
        epoch_hashes = self.epoch.get_epoch_hashes()
        for top, epoch_hash in epoch_hashes.items():
            permission = self.permissions.get_sign_permission(epoch_hash, epoch_block_number)
            if permission.public_key == self.block_signer.private_key.publickey():
                allowed_to_sign = True
                break

        block_has_not_been_signed_yet = not self.epoch.is_current_timeframe_block_present()
        if allowed_to_sign and block_has_not_been_signed_yet:
            should_skip_maliciously = self.behaviour.is_malicious_skip_block()
            first_epoch_ever = self.epoch.get_epoch_number(current_block_number) == 1
            if should_skip_maliciously and not first_epoch_ever:
                self.epoch_private_keys.clear()
                self.logger.info("Maliciously skiped block")
            else:
                self.sign_block(current_block_number)
            

    def sign_block(self, current_block_number):
        current_round_type = self.epoch.get_round_by_block_number(current_block_number)
        
        transactions = self.mempool.get_transactions_for_round(current_round_type)

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
        if conflicts: current_top_blocks += conflicts
        
        block = BlockFactory.create_block_dummy(current_top_blocks)
        block.system_txs = transactions
        signed_block = BlockFactory.sign_block(block, self.block_signer.private_key)
        self.dag.add_signed_block(current_block_number, signed_block)
        self.logger.debug("Broadcasting signed block number %s", current_block_number)
        self.network.broadcast_block(self.node_id, signed_block.pack())

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
            
        node_pubkey = self.block_signer.private_key.publickey()
        
        pubkey_publishers = []
        for _, epoch_hash in self.epoch.get_epoch_hashes().items():
            pubkey_publishers += self.permissions.get_ordered_pubkeys_for_last_round(epoch_hash)

        for publisher in pubkey_publishers:
            if node_pubkey == publisher.public_key:
                node_private = self.block_signer.private_key
                generated_private = Private.generate()
                tx = PublicKeyTransaction()
                tx.generated_pubkey = Keys.to_bytes(generated_private.publickey())
                tx.sender_pubkey = Keys.to_bytes(node_private.publickey())
                tx.signature = node_private.sign(tx.get_hash(), 0)[0]
                self.epoch_private_keys.append(generated_private)
                self.logger.debug("Broadcasted public key")
                self.logger.debug(Keys.to_visual_string(tx.generated_pubkey))
                self.mempool.add_transaction(tx)
                self.network.broadcast_transaction(self.node_id, TransactionParser.pack(tx))
    
    def try_to_share_random(self):
        pubkey = self.block_signer.private_key.publickey()
        epoch_hashes = self.epoch.get_epoch_hashes()
        for top, epoch_hash in epoch_hashes.items():
            if epoch_hash in self.sent_shares_epochs: continue
            allowed_to_share_random = self.permissions.get_secret_sharers(epoch_hash)
            if not pubkey in allowed_to_share_random: continue
            split_random = self.form_split_random_transaction(top, epoch_hash)
            self.sent_shares_epochs.append(epoch_hash)
            self.mempool.add_transaction(split_random)
            self.network.broadcast_transaction(self.node_id, TransactionParser.pack(split_random))

    def try_to_commit_random(self):
        pubkey = self.block_signer.private_key.publickey()
        epoch_hashes = self.epoch.get_epoch_hashes().values()
        for epoch_hash in epoch_hashes:
            if not epoch_hash in self.reveals_to_send:
                allowed_to_commit_list = self.permissions.get_commiters(epoch_hash)
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
            self.network.broadcast_conflicting_block(self.node_id, block.pack())
        
        self.logger.info("Forming transaction with conflicting blocks")
        self.logger.info(conflict.hex())

        penalty = PenaltyTransaction()
        penalty.conflicts = conflicts
        penalty.signature = self.block_signer.private_key.sign(penalty.get_hash(), 0)[0]
        return penalty

    def form_split_random_transaction(self, top_hash, epoch_hash):
        ordered_senders = self.permissions.get_ordered_pubkeys_for_last_round(epoch_hash)
        published_pubkeys = self.epoch.get_public_keys_for_epoch(top_hash)
        
        self.logger.info("Ordered pubkeys for secret sharing:")
        sorted_published_pubkeys = []
        for sender in ordered_senders:
            raw_sender_pubkey = Keys.to_bytes(sender.public_key)
            if raw_sender_pubkey in published_pubkeys:
                generated_pubkey = published_pubkeys[raw_sender_pubkey]
                sorted_published_pubkeys.append(Keys.from_bytes(generated_pubkey))
                self.logger.info(Keys.to_visual_string(generated_pubkey))
            else:
                sorted_published_pubkeys.append(None)
                self.logger.info("None")

        tx = self.form_secret_sharing_transaction(sorted_published_pubkeys, epoch_hash)
        return tx

    
    def form_secret_sharing_transaction(self, sorted_public_keys, epoch_hash):
        random_bytes = os.urandom(32)
        splits = split_secret(random_bytes, Duration.PRIVATE // 2 + 1, Duration.PRIVATE)
        encoded_splits = encode_splits(splits, sorted_public_keys)
        self.logger.info("Formed split random")
        
        tx = SplitRandomTransaction()
        tx.pieces = encoded_splits
        tx.signature = self.block_signer.private_key.sign(tx.get_signing_hash(epoch_hash), 0)[0]
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
            if True: #TODO: add block verification
                current_block_number = self.epoch.get_current_timeframe_block_number()
                self.dag.add_signed_block(current_block_number, signed_block)
                self.mempool.remove_transactions(block.system_txs)
            else:
                self.logger.error("Block was not added. Considered invalid")
        else:
            self.logger.error("Received block from %d, but it's signature is wrong", node_id)

    def handle_transaction_message(self, node_id, raw_transaction):
        transaction = TransactionParser.parse(raw_transaction)
        verifier = TransactionVerifier(self.dag)
        #print("Node ", self.node_id, "received transaction with hash", transaction.get_hash().hexdigest(), " from node ", node_id)
        if verifier.check_if_valid(transaction):
           # print("It is valid. Adding to mempool")
            self.mempool.add_transaction(transaction)
        else:
            self.logger.error("Received tx is invalid")

    def handle_conflicting_block_message(self, node_id, raw_signed_block):
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
            if True: #TODO: add block verification
                self.dag.add_signed_block(block_number, signed_block)
                self.mempool.remove_transactions(signed_block.block.system_txs)
            else:
                self.logger.error("Block was not added. Considered invalid")
        else:
            self.logger.error("Received block from %d, but it's signature is wrong", node_id)

    def handle_gossip_negative(self, sender_node_id, raw_gossip):
        pass

    def handle_gossip_positive(self, sender_node_id, raw_gossip):
        pass


    def get_allowed_signers_for_block_number(self, block_number):
        blocks = self.dag.blocks_by_number[block_number]
        allowed_signers = []
        epoch_block_number = self.epoch.convert_to_epoch_block_number(block_number)
        for block in blocks:
            epoch_hash = self.epoch.find_epoch_hash_for_block(block.get_hash())
            
            if epoch_hash:
                allowed_pubkey = self.permissions.get_sign_permission(epoch_hash, epoch_block_number)
                allowed_signers.append(allowed_pubkey)

        assert len(allowed_signers) > 0, "No signers allowed to sign block"
        return allowed_signers

    def broadcast_stakehold_transaction(self):
        tx = StakeHoldTransaction()
        tx.amount = 1000
        node_private = self.block_signer.private_key
        tx.pubkey = Keys.to_bytes(node_private.publickey())
        tx.signature = node_private.sign(tx.get_hash(), 0)[0]
        self.logger.info("Broadcasted StakeHold transaction")
        self.network.broadcast_transaction(self.node_id, TransactionParser.pack(tx))

    def broadcast_stakerelease_transaction(self):
        tx = StakeReleaseTransaction()
        node_private = self.block_signer.private_key
        tx.pubkey = Keys.to_bytes(node_private.publickey())
        tx.signature = node_private.sign(tx.get_hash(), 0)[0]
        self.logger.info("Broadcasted release stake transaction")
        self.network.broadcast_transaction(self.node_id, TransactionParser.pack(tx))

    def broadcast_gossip_negative(self):
        pass

    def broadcast_gossip_positive(self):
        pass

    @staticmethod
    def create_commit_reveal_pair(node_private, random_bytes, epoch_hash):
        private = Private.generate()
        public = node_private.publickey()
        encoded = private.encrypt(random_bytes, 32)[0]

        commit = CommitRandomTransaction()
        commit.rand = encoded
        commit.pubkey = Keys.to_bytes(public)
        commit.signature = node_private.sign(commit.get_signing_hash(epoch_hash), 0)[0]

        reveal = RevealRandomTransaction()
        reveal.commit_hash = commit.get_reference_hash()
        reveal.key = Keys.to_bytes(private)

        return (commit, reveal)