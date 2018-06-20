import time
import asyncio
import os

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
        self.dag = Dag(genesis_creation_time)
        self.permissions = Permissions()
        self.mempool = Mempool()
        self.epoch = Epoch(self.dag)


        self.block_signer = block_signer
        self.network = network
        self.node_id = node_id
        self.try_to_calculate_next_epoch_validators(0)
        self.epoch_private_keys = []
        #self.epoch_private_keys where first element is era number, and second is key to reveal commited random

    def start(self):
        pass

    async def run(self):
        while True:
            current_block_number = self.epoch.get_current_timeframe_block_number()
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
        epoch_number = self.epoch.get_epoch_number(current_block_number)
        epoch_block_number = self.epoch.convert_to_epoch_block_number(current_block_number)
        current_validator = self.permissions.get_permission(epoch_number, epoch_block_number)
        is_public_key_corresponds = current_validator.public_key == self.block_signer.private_key.publickey()
        block_has_not_been_signed_yet = not self.epoch.is_current_timeframe_block_present()
        if is_public_key_corresponds and block_has_not_been_signed_yet:
            if self.epoch.get_round_by_block_number(current_block_number) == Round.PRIVATE:
                self.try_to_publish_private(current_block_number) #TODO maybe should be a part of block
            transactions = self.mempool.get_transactions_for_round(self.epoch.get_current_round())
            penalty = self.form_penalize_violators_transaction(current_block_number)
            if penalty : transactions.append(penalty)
            current_top_blocks = self.dag.get_top_blocks()
            block = BlockFactory.create_block_dummy(current_top_blocks)
            block.system_txs = transactions
            signed_block = BlockFactory.sign_block(block, self.block_signer.private_key)
            self.dag.add_signed_block(current_block_number, signed_block)
            self.try_to_calculate_next_epoch_validators(current_block_number)             
            self.network.broadcast_block(self.node_id, signed_block.pack())

            if self.permissions.is_malicious(self.node_id):
                additional_block_timestamp = block.timestamp + 1
                block = BlockFactory.create_block_with_timestamp(current_top_blocks, additional_block_timestamp)
                block.system_txs = transactions.copy()
                signed_block = BlockFactory.sign_block(block, self.block_signer.private_key)
                self.dag.add_signed_block(current_block_number, signed_block)
                self.network.broadcast_block(self.node_id, signed_block.pack())
                print("Node", self.node_id, "has sent additional block")


    def try_to_publish_public_key(self, current_block_number):
        epoch_number = self.epoch.get_epoch_number(current_block_number)

        if self.epoch_private_keys:
            return
            
        node_pubkey = self.block_signer.private_key.publickey()
        pubkey_publishers = self.permissions.get_ordered_pubkeys_for_last_round(epoch_number, Round.PRIVATE_DURATION)
        for publisher in pubkey_publishers:
            if node_pubkey == publisher:
                node_private = self.block_signer.private_key
                generated_private = Private.generate()
                tx = PublicKeyTransaction()
                tx.generated_pubkey = Keys.to_bytes(generated_private.publickey())
                tx.sender_pubkey = Keys.to_bytes(node_private.publickey())
                tx.signature = node_private.sign(tx.get_hash(), 0)[0]
                self.epoch_private_keys.append(generated_private)
                print("Node ", self.node_id, "broadcasted public key")
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
            print("Node", self.node_id, "sent private key")

    def form_penalize_violators_transaction(self, current_block_number):
        merger = Merger(self.dag)
        conflicts = merger.get_conflicts()

        if conflicts:
            for conflict in conflicts:
                block = self.dag.blocks_by_hash[conflict]
                self.network.broadcast_block(self.node_id, block.pack())
            
            print("found conflicting blocks")
            print(conflict)

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

        ordered_senders_pubkeys = self.permissions.get_ordered_pubkeys_for_last_round(epoch_number, Round.PRIVATE_DURATION)
        published_pubkeys = self.epoch.get_public_keys_for_epoch(epoch_number)
        
        print("ordered pubkeys")
        sorted_published_pubkeys = []
        for sender_pubkey in ordered_senders_pubkeys:
            generated_pubkeys = published_pubkeys[Keys.to_bytes(sender_pubkey)]
            pubkey = generated_pubkeys.pop(0) #TODO come up with some ordering guarantees
            sorted_published_pubkeys.append(Keys.from_bytes(pubkey))
            Keys.display(pubkey)
        
        random_bytes = os.urandom(32)
        splits = split_secret(random_bytes, Round.PRIVATE_DURATION // 2 + 1, Round.PRIVATE_DURATION)
        encoded_splits = encode_splits(splits, sorted_published_pubkeys)
        print("Node", self.node_id, "broadcasting random")
        
        self.last_epoch_random_published = epoch_number 

        tx = SplitRandomTransaction()
        tx.pieces = encoded_splits
        tx.signature = self.block_signer.private_key.sign(tx.get_hash(), 0)[0]
        self.mempool.add_transaction(tx)
        self.network.broadcast_transaction(self.node_id, TransactionParser.pack(tx))
    
    def handle_block_message(self, node_id, raw_signed_block):
        current_block_number = self.epoch.get_current_timeframe_block_number()
        epoch_number = self.epoch.get_epoch_number(current_block_number)
        epoch_block_number = self.epoch.convert_to_epoch_block_number(current_block_number)
        current_validator = self.permissions.get_permission(epoch_number, epoch_block_number)
        signed_block = SignedBlock()
        signed_block.parse(raw_signed_block)

        if signed_block.verify_signature(current_validator.public_key):
            block = signed_block.block
            if True: #TODO: add block verification
                self.dag.add_signed_block(current_block_number, signed_block)
                self.mempool.remove_transactions(block.system_txs)
                self.try_to_calculate_next_epoch_validators(current_block_number)
            else:
                print("Block was not added. Considered invalid")
        else:
            print("Node", node_id, "sent block, but it's signature is wrong")
            self.network.gossip_malicious(current_validator.public_key)

    def try_to_calculate_next_epoch_validators(self, current_block_number):
        if self.epoch.is_last_block_of_era(current_block_number):
            next_epoch_number = self.epoch.get_epoch_number(current_block_number) + 1
            validators_count = self.permissions.get_validators_count()
            validators_list = self.epoch.calculate_validators_numbers(next_epoch_number, validators_count)
            print("calculated validators list for node ", self.node_id, validators_list)
            self.permissions.set_validators_list(next_epoch_number, validators_list)

    def handle_transaction_message(self, node_id, raw_transaction):
        transaction = TransactionParser.parse(raw_transaction)
        verifier = TransactionVerifier(self.dag)
        #print("Node ", self.node_id, "received transaction with hash", transaction.get_hash().hexdigest(), " from node ", node_id)
        if verifier.check_if_valid(transaction):
           # print("It is valid. Adding to mempool")
            self.mempool.add_transaction(transaction)
        else:
            print("It's invalid. Do something about it")


