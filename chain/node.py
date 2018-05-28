import time
import asyncio

from chain.node_api import NodeApi
from chain.dag import Dag
from chain.block_signers import BlockSigners
from chain.permissions import Permissions
from chain.signed_block import SignedBlock
from transaction.mempool import Mempool
from transaction.transaction import TransactionParser, CommitRandomTransaction
from crypto.enc_random import enc_part_random

class Node():
    
    def __init__(self, genesis_creation_time, node_id, network, block_signer):
        self.dag = Dag(genesis_creation_time)
        self.permissions = Permissions()
        self.mempool = Mempool()
        
        self.block_signer = block_signer
        self.network = network
        self.node_id = node_id
        #self.last_commited_random_key where first element is era number, and second is key to reveal commited random

    def start(self):
        pass

    async def run(self):
        while True:
            self.try_to_commit_random()
            self.try_to_sign_block()
            await asyncio.sleep(3)

    def try_to_sign_block(self):
        current_block_validator = self.permissions.get_permission(self.dag, self.dag.get_current_timeframe_block_number())
        is_public_key_corresponds = current_block_validator.public_key == self.block_signer.private_key.publickey()
        block_has_not_been_signed_yet = not self.dag.is_current_timeframe_block_present()
        if is_public_key_corresponds and block_has_not_been_signed_yet:
            signed_block = self.dag.sign_block(self.block_signer.private_key)
            raw_signed_block = signed_block.pack();
            self.network.broadcast_block(self.node_id, raw_signed_block) 

    def try_to_commit_random(self):
        current_block_number = self.dag.get_current_timeframe_block_number()
        era_number = self.dag.get_era_number(current_block_number)
        has_reveal_key = hasattr(self, "last_commited_random_key")
        has_key_for_previous_era = has_reveal_key and self.last_commited_random_key[0] < era_number
        if not has_reveal_key or has_key_for_previous_era:
            era_hash = self.dag.get_era_hash(era_number)
            tx = CommitRandomTransaction()
            data, key = enc_part_random(era_hash)
            tx.rand = data
            raw_tx = TransactionParser.pack(tx)
            self.last_commited_random_key = (era_number, key)
            self.network.broadcast_transaction(self.node_id, raw_tx)

    def handle_block_message(self, node_id, raw_signed_block):
        current_block_number = self.dag.get_current_timeframe_block_number()
        current_validator = self.permissions.get_permission(self.dag, current_block_number)
        signed_block = SignedBlock()
        signed_block.parse(raw_signed_block)
        print("Node ", self.node_id, "received block from node", node_id, "with block hash", signed_block.block.get_hash().hexdigest())
        if signed_block.verify_signature(current_validator.public_key):
            self.dag.add_signed_block(current_block_number, signed_block)
        else:
            self.network.gossip_malicious(current_validator.public_key)

    def handle_transaction_message(self, node_id, raw_transaction):
        transaction = TransactionParser.parse(raw_transaction)
        print("Node ", self.node_id, "received transaction with hash", transaction.get_hash().hexdigest(), " from node ", node_id)
        self.mempool.add_transaction(transaction)     


