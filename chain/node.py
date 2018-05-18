import time
from chain.node_api import NodeApi
from chain.dag import Dag
from chain.block_signers import BlockSigners
from chain.permissions import Permissions

class Node():
    
    def __init__(self, genesis_creation_time):
        self.dag = Dag(genesis_creation_time)
        self.network = NodeApi(self)
        self.block_signers = BlockSigners()
        self.permissions = Permissions()

    def start(self):
        pass

    def run(self):
        while True:
            for block_singer in self.block_signers.block_signers:
                current_block_validator = self.permissions.get_permission(self.dag, self.dag.get_current_timeframe_block_number())
                if current_block_validator.public_key == block_singer.private_key.publickey():
                    signed_block = self.dag.sign_block(block_singer.private_key)
                    raw_signed_block = signed_block.pack();
                    self.network.broadcast_block(raw_signed_block)
            time.sleep(5)

    def handle_block_message(self, raw_signed_block):
        current_block_number = self.dag.get_current_timeframe_block_number()
        current_validator = self.permissions.get_permission(self.dag, current_timeframe_node_number)
        signed_block = SignedBlock()
        signed_block.parse(raw_signed_block)
        if signed_block.verify_signature(current_validator.public_key):
            self.dag.add_signed_block(signed_block)
        else:
            self.network.gossip_malicious(current_validator.public_key)
            


