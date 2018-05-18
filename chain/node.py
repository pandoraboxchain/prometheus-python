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

    def loop(self):
        while True:
            time.sleep(10)
            for block_singer in self.block_signers.block_signers:
                if self.permissions(self.dag, )
            signed_block = self.dag.sign_block()
            self.node_api.push_block(signed_block.pack())


