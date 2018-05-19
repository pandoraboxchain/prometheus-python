import time
import asyncio

from chain.node_api import NodeApi
from chain.dag import Dag
from chain.block_signers import BlockSigners
from chain.permissions import Permissions
from chain.signed_block import SignedBlock

class Node():
    
    def __init__(self, genesis_creation_time, node_id, network, block_signer):
        self.dag = Dag(genesis_creation_time)
        self.permissions = Permissions()
        
        self.block_signer = block_signer
        self.network = network
        self.node_id = node_id

    def start(self):
        pass

    async def run(self):
        while True:
            current_block_validator = self.permissions.get_permission(self.dag, self.dag.get_current_timeframe_block_number())
            is_public_key_corresponds = current_block_validator.public_key == self.block_signer.private_key.publickey()
            block_has_not_been_signed_yet = not self.dag.is_current_timeframe_block_present()
            if is_public_key_corresponds and block_has_not_been_signed_yet:
                signed_block = self.dag.sign_block(self.block_signer.private_key)
                raw_signed_block = signed_block.pack();
                self.network.broadcast_block(self.node_id, raw_signed_block)
            await asyncio.sleep(3)

    def handle_block_message(self, node_id, raw_signed_block):
        current_block_number = self.dag.get_current_timeframe_block_number()
        current_validator = self.permissions.get_permission(self.dag, current_block_number)
        signed_block = SignedBlock()
        signed_block.parse(raw_signed_block)
        print("Node number", self.node_id, "received block from node", node_id, "with block hash", signed_block.block.get_hash().hexdigest())
        if signed_block.verify_signature(current_validator.public_key):
            self.dag.add_signed_block(signed_block)
        else:
            self.network.gossip_malicious(current_validator.public_key)
            


