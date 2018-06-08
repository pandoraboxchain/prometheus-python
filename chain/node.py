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
from transaction.mempool import Mempool
from transaction.transaction import TransactionParser, CommitRandomTransaction, RevealRandomTransaction
from transaction.transaction import PublicKeyTransaction, PrivateKeyTransaction, SplitRandomTransaction
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
        #self.epoch_private_key where first element is era number, and second is key to reveal commited random

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
            await asyncio.sleep(3)

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
            block = BlockFactory.create_block_dummy(self.dag.get_top_blocks())
            block.system_txs = transactions
            signed_block = BlockFactory.sign_block(block, self.block_signer.private_key)
            self.dag.add_signed_block(current_block_number, signed_block)
            raw_signed_block = signed_block.pack()
            self.try_to_calculate_next_epoch_validators(current_block_number)            
            self.network.broadcast_block(self.node_id, raw_signed_block) 

    def try_to_publish_public_key(self, current_block_number):
        epoch_number = self.epoch.get_epoch_number(current_block_number)

        node_pubkey = self.block_signer.private_key.publickey()
        pubkey_publishers = self.permissions.get_ordered_pubkeys_for_last_round(epoch_number, Round.PRIVATE_DURATION)
        if not node_pubkey in pubkey_publishers:
            return

        has_key = hasattr(self, "epoch_private_key")
        has_key_for_previous_epoch = has_key and self.epoch_private_key[0] < epoch_number
        if not has_key or has_key_for_previous_epoch:
            node_private = self.block_signer.private_key
            generated_private = Private.generate()
            tx = PublicKeyTransaction()
            tx.generated_pubkey = Keys.to_bytes(generated_private.publickey())
            tx.sender_pubkey = Keys.to_bytes(node_private.publickey())
            tx.signature = node_private.sign(tx.get_hash().digest(), 0)[0]
            self.epoch_private_key = (epoch_number, generated_private)
            print("Node ", self.node_id, "broadcasted public key")
            self.mempool.add_transaction(tx)
            self.network.broadcast_transaction(self.node_id, TransactionParser.pack(tx))

    def try_to_publish_private(self, current_block_number):
        epoch_number = self.epoch.get_epoch_number(current_block_number)
        has_key = hasattr(self, "epoch_private_key")
        has_key_for_this_epoch = has_key and self.epoch_private_key[0] == epoch_number
        if has_key and has_key_for_this_epoch:
            tx = PrivateKeyTransaction()
            tx.key = Keys.to_bytes(self.epoch_private_key[1])
            del self.epoch_private_key
            self.mempool.add_transaction(tx)
            self.network.broadcast_transaction(self.node_id, TransactionParser.pack(tx))

    def try_to_send_split_random(self, current_block_number):    
        epoch_number = self.epoch.get_epoch_number(current_block_number)
        if hasattr(self,"last_epoch_random_published"):
             if epoch_number == self.last_epoch_random_published:
                 return

        #FIXME here is the hole in logic
        #this pubkeys must be not signers pubkeys, but theirs published pubkeys
        ordered_pubkeys = self.permissions.get_ordered_pubkeys_for_last_round(epoch_number, Round.PRIVATE_DURATION)
        random_bytes = os.urandom(32)
        splits = split_secret(random_bytes, Round.PRIVATE_DURATION // 2 + 1, Round.PRIVATE_DURATION)
        encoded_splits = encode_splits(splits, ordered_pubkeys)
        
        self.last_epoch_random_published = epoch_number 

        tx = SplitRandomTransaction()
        tx.pieces = encoded_splits
        tx.signature = self.block_signer.private_key.sign(tx.get_hash().digest(), 0)[0]
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
                self.try_to_calculate_next_epoch_validators(current_block_number)
                print("Node ", self.node_id, "received block from node", node_id, "with block hash", signed_block.block.get_hash().hexdigest())
            else:
                print("Block was not added. Considered invalid")
        else:
            print("Node", node_id, "sent block, though it's not her time")
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


