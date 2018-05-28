from chain.node import Node
from chain.node_api import NodeApi
from chain.block_signers import BlockSigners

import datetime
import time
import asyncio

class Initializer():  

    def __init__(self):
        BLOCK_TIME = 5  #TODO merge this value woth Dag value
        genesis_creation_time = int(datetime.datetime.now().timestamp() - BLOCK_TIME)
        print("genesis_creation_time", genesis_creation_time)

        private_keys = BlockSigners()

        network = NodeApi()

        tasks = []
         
        for i in range(0, 10):
            node =  Node(genesis_creation_time, i, network, private_keys.block_signers[i])
            network.register_node(node)
            tasks.append(node.run())  

        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(*tasks))       
        loop.close()
        
Initializer()