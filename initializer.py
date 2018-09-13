from chain.node import Node
from chain.node_api import NodeApi
from chain.block_signers import BlockSigners
from chain.block_signer import BlockSigner
from chain.epoch import BLOCK_TIME
from chain.behaviour import Behaviour
from crypto.private import Private
from tools.announcer_node import AnnouncerNode
from tools.time import Time

from tools.time import Time
import time
import asyncio
import logging
import sys
import importlib
import datetime

#you can set node to visualize its DAG as soon as Ctrl-C pressed
def save_dag_to_graphviz(dag_to_visualize):
    graphviz_import = importlib.util.find_spec("graphviz")
    graphviz_lib_installed = graphviz_import is not None
    if graphviz_lib_installed:
        from visualization.dag_visualizer import DagVisualizer
        DagVisualizer.visualize(dag_to_visualize)

class Initializer(): 

    def __init__(self):
        node_to_visualize_after_exit = None
        try:
            # set up logging to file - see previous section for more details
            logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)-6s %(name)-6s %(message)s')

            Time.set_current_time(int(datetime.datetime.now().timestamp()))
            genesis_creation_time = Time.get_current_time() - BLOCK_TIME #so we start right from the first block

            private_keys = BlockSigners()

            network = NodeApi()

            tasks = []

            logger = logging.getLogger("Announce")
            announcer = AnnouncerNode(genesis_creation_time, logger)
            tasks.append(announcer.run())
            
            for i in range(0, 19):
                behaviour = Behaviour()

                if i==7:
                    behaviour.malicious_wrong_signature = True

                logger = logging.getLogger("Node " + str(i))
                # uncomment the following line to enable logging only on specific node
                if i != 13: logger.setLevel(logging.CRITICAL)
                node = Node(genesis_creation_time, i, network, logger, private_keys.block_signers[i], behaviour)

                if i == 0: node_to_visualize_after_exit = node
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

            loop = asyncio.get_event_loop()
            loop.run_until_complete(asyncio.gather(*tasks))       
            loop.close()
        
        finally:
            if node_to_visualize_after_exit:
                save_dag_to_graphviz(node_to_visualize_after_exit.dag)

        
Initializer()