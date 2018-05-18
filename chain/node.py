import time
from node_api import NodeApi
from dag import Dag
from block_signers import BlockSigners
from permissions import Permissions

class Node():
    
    def __init__(self, genesis_creation_time):
        self.dag = Dag(genesis_creation_time)
        self.network = NodeApi()
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
                    NodeApi.broadcast_block(raw_signed_block)
            time.sleep(5)
            


