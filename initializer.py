from chain.node import Node
from chain.node_api import NodeApi

import datetime
import time
import asyncio

class Initializer():  
    
    def __init__(self):
        genesis_creation_time = int(datetime.datetime.now().timestamp())
        print("genesis_creation_time", genesis_creation_time)

        network = NodeApi()

        node1 = Node(genesis_creation_time, 1, network)
        node2 = Node(genesis_creation_time, 2, network)   

        network.register_node(node1)
        network.register_node(node2)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(node1.run())
        loop.run_until_complete(node2.run())        
        loop.close()
        
Initializer()