from chain.node import Node
from chain.node_api import NodeApi
from chain.block_signers import BlockSigners
from chain.epoch import BLOCK_TIME
from chain.behaviour import Behaviour

import datetime
import time
import asyncio
import logging
import sys

class Initializer():  

    def __init__(self):
        
        # set up logging to file - see previous section for more details
        logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-6s %(name)-6s %(message)s')

        genesis_creation_time = int(datetime.datetime.now().timestamp() - BLOCK_TIME) #so we start right from the first block

        private_keys = BlockSigners()

        network = NodeApi()

        tasks = []
         
        for i in range(0, 9):
            behaviour = Behaviour()
            node =  Node(genesis_creation_time, i, network, private_keys.block_signers[i], behaviour)
            network.register_node(node)
            tasks.append(node.run())

        for i in range(9, 10):
            behaviour = Behaviour()
            behaviour.wants_to_hold_stake = True
            behaviour.epoch_to_release_stake = 2
            keyless_node = Node(genesis_creation_time, i, network, None, behaviour)
            network.register_node(keyless_node)
            tasks.append(keyless_node.run())

        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(*tasks))       
        loop.close()
        
Initializer()