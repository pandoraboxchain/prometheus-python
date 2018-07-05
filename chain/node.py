import time
import asyncio
import os
import logging

from base64 import b64decode,b64encode

from chain.node_api import NodeApi
from chain.dag import Dag
from chain.epoch import Round, Epoch
from chain.block_signers import BlockSigners
from chain.permissions import Permissions
from chain.signed_block import SignedBlock
from chain.block_factory import BlockFactory
from chain.merger import Merger
from transaction.mempool import Mempool
from transaction.transaction import TransactionParser
from transaction.transaction import PublicKeyTransaction, PrivateKeyTransaction, SplitRandomTransaction
from transaction.stake_transaction import StakeHoldTransaction, PenaltyTransaction
from verification.transaction_verifier import TransactionVerifier
from verification.block_verifier import BlockVerifier
from crypto.enc_random import enc_part_random
from crypto.keys import Keys
from crypto.private import Private
from transaction.commits_set import CommitsSet
from crypto.secret import split_secret, encode_splits, decode_random

class Node():
    
    def __init__(self, genesis_creation_time, node_id, network, block_signer):
        self.logger = logging.getLogger("Node " + str(node_id))
        self.dag = Dag(genesis_creation_time)
        self.epoch = Epoch(self.dag)
        self.dag.subscribe_to_new_block_notification(self.epoch)
        self.permissions = Permissions(self.epoch)
        self.mempool = Mempool()


        self.block_signer = block_signer
        self.network = network
        self.node_id = node_id
        self.epoch_private_keys = []
        #self.epoch_private_keys where first element is era number, and second is key to reveal commited random

    def start(self):
        pass

    async def run(self):
        while True:
            current_block_number = self.epoch.get_current_timeframe_block_number()
            self.epoch.check_if_new_epoch_and_update_hashes(current_block_number)
            # self.mempool.remove_all_systemic_transactions()

            if self.epoch.get_round_by_block_number(current_block_number) == Round.PUBLIC:
                self.try_to_publish_public_key(current_block_number)
            elif self.epoch.get_round_by_block_number(current_block_number) == Round.RANDOM:
                self.try_to_send_split_random(current_block_number)
            elif self.epoch.get_round_by_block_number(current_block_number) == Round.PRIVATE:
                #delete random if we published it in previous round
                #real private key publish will happen when signing block
                if hasattr(self, "self.last_epoch_random_published"):
                    del self.last_epoch_random_published
                              
            self.try_to_sign_block(current_block_number)

            await asyncio.sleep(1)
    
    def try_to_sign_block(self, current_block_number):        
        epoch_block_number = self.epoch.convert_to_epoch_block_number(current_block_number)
        
        allowed_to_sign = False
        epoch_hashes = self.epoch.get_epoch_hashes()
        for top, epoch_hash in epoch_hashes.items():
            permission = self.permissions.get_permission(epoch_hash, epoch_block_number)
            if permission.public_key == self.block_signer.private_key.publickey():
                allowed_to_sign = True
                break

        block_has_not_been_signed_yet = not self.epoch.is_current_timeframe_block_present()
        if allowed_to_sign and block_has_not_been_signed_yet:
            if self.permissions.is_malicious_skip_block(self.node_id):
                self.logger.info("Maliciously skiped block")
            else:
                self.sign_block(current_block_number)
            

    def sign_block(self, current_block_number):
        if self.epoch.get_round_by_block_number(current_block_number) == Round.PRIVATE:
            self.try_to_publish_private(current_block_number) #TODO maybe should be a part of block
        transactions = self.mempool.get_transactions_for_round(self.epoch.get_current_round())
        penalty = self.form_penalize_violators_transaction(current_block_number)
        if penalty : transactions.append(penalty)
        current_top_blocks = self.dag.get_top_blocks_hashes()
        block = BlockFactory.create_block_dummy(current_top_blocks)
        block.system_txs = transactions
        signed_block = BlockFactory.sign_block(block, self.block_signer.private_key)
        self.dag.add_signed_block(current_block_number, signed_block)
        self.logger.info("Block signed by node")
        self.network.broadcast_block(self.node_id, signed_block.pack())

        if self.permissions.is_malicious_excessive_block(self.node_id):
            additional_block_timestamp = block.timestamp + 1
            block = BlockFactory.create_block_with_timestamp(current_top_blocks, additional_block_timestamp)
            block.system_txs = transactions.copy()
            signed_block = BlockFactory.sign_block(block, self.block_signer.private_key)
            self.dag.add_signed_block(current_block_number, signed_block)
            self.network.broadcast_block(self.node_id, signed_block.pack())
            self.logger.info("Sent additional block")

    def try_to_publish_public_key(self, current_block_number):
        if self.epoch_private_keys:
            return
            
        node_pubkey = self.block_signer.private_key.publickey()
        
        pubkey_publishers = []
        for _, epoch_hash in self.epoch.get_epoch_hashes().items():
            pubkey_publishers += self.permissions.get_ordered_pubkeys_for_last_round(epoch_hash, Round.PRIVATE_DURATION)

        for publisher in pubkey_publishers:
            if node_pubkey == publisher:
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

    def try_to_publish_private(self, current_block_number):
        epoch_number = self.epoch.get_epoch_number(current_block_number)
        if self.epoch_private_keys:
            tx = PrivateKeyTransaction()
            tx.key = Keys.to_bytes(self.epoch_private_keys.pop(0))
            self.mempool.add_transaction(tx)
            # intentionally do not broadcast transaction since private key better be part of a block
            # only one private key tx should be in a block
            # self.network.broadcast_transaction(self.node_id, TransactionParser.pack(tx))
            self.logger.info("Sent private key")

    def form_penalize_violators_transaction(self, current_block_number):
        merger = Merger(self.dag)
        conflicts = merger.get_conflicts()

        if conflicts:
            for conflict in conflicts:
                block = self.dag.blocks_by_hash[conflict]
                self.network.broadcast_block(self.node_id, block.pack())
            
            self.logger.info("found conflicting blocks")
            self.logger.info(conflict.hex())

            penalty = PenaltyTransaction()
            penalty.conflicts = conflicts
            penalty.signature = self.block_signer.private_key.sign(penalty.get_hash(), 0)[0]
            return penalty
        
        return None


    def try_to_send_split_random(self, current_block_number):    
        epoch_number = self.epoch.get_epoch_number(current_block_number)
        if hasattr(self,"last_epoch_random_published"):
            if epoch_number == self.last_epoch_random_published:
                return

        epoch_hashes = self.epoch.get_epoch_hashes()
        
        for top_hash, epoch_hash in epoch_hashes.items():
            ordered_senders_pubkeys = self.permissions.get_ordered_pubkeys_for_last_round(epoch_hash, Round.PRIVATE_DURATION)
            published_pubkeys = self.epoch.get_public_keys_for_epoch(top_hash)
            
            self.logger.info("Ordered pubkeys for secret sharing:")
            sorted_published_pubkeys = []
            for sender_pubkey in ordered_senders_pubkeys:
                raw_sender_pubkey = Keys.to_bytes(sender_pubkey)
                if raw_sender_pubkey in published_pubkeys:
                    generated_pubkey = published_pubkeys[raw_sender_pubkey]
                    sorted_published_pubkeys.append(Keys.from_bytes(generated_pubkey))
                    self.logger.info(Keys.to_visual_string(generated_pubkey))
                else:
                    sorted_published_pubkeys.append(None)
                    self.logger.info("None")

            tx = self.form_transaction_for_random(sorted_published_pubkeys)

            self.mempool.add_transaction(tx)
            self.network.broadcast_transaction(self.node_id, TransactionParser.pack(tx))  
        
        self.last_epoch_random_published = epoch_number    
    
    def form_transaction_for_random(self, sorted_public_keys):
        random_bytes = os.urandom(32)
        splits = split_secret(random_bytes, Round.PRIVATE_DURATION // 2 + 1, Round.PRIVATE_DURATION)
        encoded_splits = encode_splits(splits, sorted_public_keys)
        self.logger.info("Broadcasting random")
        
        tx = SplitRandomTransaction()
        tx.pieces = encoded_splits
        tx.signature = self.block_signer.private_key.sign(tx.get_hash(), 0)[0]
        return tx

    def get_allowed_signers_for_next_block(self, block):
        current_block_number = self.epoch.get_current_timeframe_block_number()
        epoch_block_number = self.epoch.convert_to_epoch_block_number(current_block_number)
        self.epoch.check_if_new_epoch_and_update_hashes(current_block_number)
        epoch_hashes = self.epoch.get_epoch_hashes()
        allowed_signers = []
        for prev_hash in block.prev_hashes:
            epoch_hash = None
            if prev_hash in epoch_hashes:
                epoch_hash = epoch_hashes[prev_hash]
            else:
                epoch_hash = self.epoch.find_epoch_hash_for_block(prev_hash)
            
            if epoch_hash:
                permission = self.permissions.get_permission(epoch_hash, epoch_block_number)
                allowed_signers.append(permission.public_key)

        assert len(allowed_signers) > 0, "No signers allowed to sign next block"
        return allowed_signers


    def handle_block_message(self, node_id, raw_signed_block):
        signed_block = SignedBlock()
        signed_block.parse(raw_signed_block)
        
        allowed_signers = self.get_allowed_signers_for_next_block(signed_block.block)

        is_block_allowed = False
        for allowed_signer in allowed_signers:
            if signed_block.verify_signature(allowed_signer):
                is_block_allowed = True
        
        if is_block_allowed:
            block = signed_block.block
            if True: #TODO: add block verification
                current_block_number = self.epoch.get_current_timeframe_block_number()
                self.logger.debug("Adding block %s", current_block_number)
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


