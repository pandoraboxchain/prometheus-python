from chain.node import Node
from chain.node_api import NodeApi
from chain.block_signers import BlockSigners
from chain.block_signer import BlockSigner
from chain.epoch import BLOCK_TIME
from chain.behaviour import Behaviour
from crypto.private import Private

import datetime
import time
import asyncio
import logging
import signal
import sys
import importlib

#you can set node to visualize its DAG as soon as Ctrl-C pressed
node_to_visualize = None
def signal_handler(sig, frame):
    graphviz_import = importlib.util.find_spec("graphviz")
    graphviz_lib_installed = graphviz_import is not None
    if node_to_visualize and graphviz_lib_installed:
        from visualization.dag_visualizer import DagVisualizer
        DagVisualizer.visualize(node_to_visualize.dag)
    sys.exit(0)

class Initializer(): 

    def __init__(self):
        
        # set up logging to file - see previous section for more details
        logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-6s %(name)-6s %(message)s')

        genesis_creation_time = int(datetime.datetime.now().timestamp() - BLOCK_TIME) #so we start right from the first block

        private_keys = BlockSigners()

        network = NodeApi()

        tasks = []
         
        for i in range(0, 19):
            behaviour = Behaviour()
            logger = logging.getLogger("Node " + str(i))
            # uncomment the following line to enable logging only on specific node
            # if i != 13: logger.setLevel(logging.CRITICAL)
            node = Node(genesis_creation_time, i, network, logger, private_keys.block_signers[i], behaviour)

            if i == 0:
                global node_to_visualize
                node_to_visualize = node
            network.register_node(node)
            tasks.append(node.run())

        for i in range(19, 20):
            behaviour = Behaviour()
            behaviour.wants_to_hold_stake = True
            behaviour.epoch_to_release_stake = 2
            logger = logging.getLogger("Node " + str(i))
            keyless_node = Node(genesis_creation_time, i, network, logger, None, behaviour)
            network.register_node(keyless_node)
            tasks.append(keyless_node.run())

        signal.signal(signal.SIGINT, signal_handler)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(*tasks))       
        loop.close()
        
Initializer()