import time
import asyncio

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
from verification.transaction_verifier import TransactionVerifier
from verification.block_verifier import BlockVerifier
from crypto.enc_random import enc_part_random
from transaction.commits_set import CommitsSet

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
        #self.last_commited_random_key where first element is era number, and second is key to reveal commited random

    def start(self):
        pass

    async def run(self):
        while True:
            current_block_number = self.epoch.get_current_timeframe_block_number()
            if self.epoch.get_round_by_block_number(current_block_number) == Round.PUBLIC:
                self.try_to_commit_random(current_block_number)
            elif self.epoch.get_round_by_block_number(current_block_number) == Round.RANDOM:
                self.try_to_reveal_random(current_block_number)
                              
            self.try_to_sign_block(current_block_number)
            await asyncio.sleep(3)

    def try_to_sign_block(self, current_block_number):
        epoch_number = self.epoch.get_epoch_number(current_block_number)
        epoch_block_number = self.epoch.convert_to_epoch_block_number(current_block_number)
        current_validator = self.permissions.get_permission(epoch_number, epoch_block_number)
        is_public_key_corresponds = current_validator.public_key == self.block_signer.private_key.publickey()
        block_has_not_been_signed_yet = not self.epoch.is_current_timeframe_block_present()
        if is_public_key_corresponds and block_has_not_been_signed_yet:
            transactions = self.mempool.get_transactions_for_round(self.epoch.get_current_round())
            block = BlockFactory.create_block_dummy(self.dag.get_top_blocks())
            block.system_txs = transactions
            signed_block = BlockFactory.sign_block(block, self.block_signer.private_key)
            self.dag.add_signed_block(current_block_number, signed_block)
            raw_signed_block = signed_block.pack();
            self.try_to_calculate_next_epoch_validators(current_block_number)            
            self.network.broadcast_block(self.node_id, raw_signed_block) 

    def try_to_commit_random(self, current_block_number):
        era_number = self.epoch.get_epoch_number(current_block_number)
        has_reveal_key = hasattr(self, "last_commited_random_key")
        has_key_for_previous_era = has_reveal_key and self.last_commited_random_key[0] < era_number
        if not has_reveal_key or has_key_for_previous_era:
            era_hash = self.epoch.get_epoch_hash(era_number)
            private = self.block_signer.private_key
            tx = CommitRandomTransaction()
            data, key = enc_part_random(era_hash)
            tx.rand = data
            tx.pubkey = b64encode(private.publickey().exportKey('DER'))
            commit_hash = tx.get_hash().digest()
            print("commit tx", commit_hash.hex())
            tx.signature = private.sign(commit_hash, 0)[0]
            raw_tx = TransactionParser.pack(tx)
            self.last_commited_random_key = (era_number, commit_hash, key)
            self.network.broadcast_transaction(self.node_id, raw_tx)
    
    def try_to_reveal_random(self, current_block_number):
        era_number = self.epoch.get_epoch_number(current_block_number)
        has_reveal_key = hasattr(self, "last_commited_random_key")
        has_key_for_this_era = has_reveal_key and self.last_commited_random_key[0] == era_number
        if has_reveal_key and has_key_for_this_era:
            tx = RevealRandomTransaction()
            tx.commit_hash = self.last_commited_random_key[1]
            print("reveal tx for ", tx.commit_hash.hex())            
            key = b64encode(self.last_commited_random_key[2].exportKey('DER'))
            tx.key = key
            raw_tx = TransactionParser.pack(tx)
            del self.last_commited_random_key
            self.network.broadcast_transaction(self.node_id, raw_tx)

    def handle_block_message(self, node_id, raw_signed_block):
        current_block_number = self.epoch.get_current_timeframe_block_number()
        epoch_number = self.epoch.get_epoch_number(current_block_number)
        epoch_block_number = self.epoch.convert_to_epoch_block_number(current_block_number)
        current_validator = self.permissions.get_permission(epoch_number, epoch_block_number)
        signed_block = SignedBlock()
        signed_block.parse(raw_signed_block)
        print("Node ", self.node_id, "received block from node", node_id, "with block hash", signed_block.block.get_hash().hexdigest())
        if signed_block.verify_signature(current_validator.public_key):
            block = signed_block.block
            print("prev_hash[0]", block.prev_hashes[0].hex())
            commits_set = CommitsSet(self.epoch, epoch_number, block.prev_hashes[0])
            if BlockVerifier.check_if_valid(block, commits_set):
                self.dag.add_signed_block(current_block_number, signed_block)
                self.try_to_calculate_next_epoch_validators(current_block_number)
                print("Block was added under number", current_block_number)
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


