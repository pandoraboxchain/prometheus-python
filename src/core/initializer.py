import datetime
import logging
import signal
import sys
import importlib

from core.node.node import Node
from core.chain.node_api import NodeApi
from core.chain.block_signers import BlockSigners
from core.chain.epoch import BLOCK_TIME
from core.chain.behaviour import Behaviour
from core.tools.visualization.dag_visualizer import DagVisualizer

# you can set node to visualize its DAG as soon as Ctrl-C pressed
# TODO ADD CONSOLE LAUNCH SHALL WITH COMMANDS AND HELP
node_to_visualize = None


def signal_handler(sig, frame):
    graphviz_import = importlib.util.find_spec("graphviz")
    graphviz_lib_installed = graphviz_import is not None
    if node_to_visualize and graphviz_lib_installed:
        DagVisualizer().visualize(node_to_visualize.dag)
    sys.exit(0)


class Initializer:

    def __init__(self):
        # set up logging to file - see previous section for more details
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)-6s %(name)-6s %(message)s')
        # so we start right from the first block
        genesis_creation_time = int(datetime.datetime.now().timestamp() - BLOCK_TIME)
        private_keys = BlockSigners()
        network = NodeApi()
        tasks = []

        nodes = []
        for i in range(0, 19):
            behaviour = Behaviour()
            # uncomment the following line to enable logging only on specific node
            # if i != 13: logger.setLevel(logging.CRITICAL)

            # init node
            node = Node(node_index=i,
                        network=network,
                        block_signer=private_keys.block_signers[i],
                        behaviour=behaviour,
                        launch_mode=0)

            if i == 0:
                global node_to_visualize
                node_to_visualize = node
            network.register_node(node)
            nodes.append(node)

        for i in range(19, 20):
            behaviour = Behaviour()
            behaviour.wants_to_hold_stake = True
            behaviour.epoch_to_release_stake = 2

            block_signers = BlockSigners()
            #block_signers.set_private_key(Private.generate())

            keyless_node = Node(node_index=i,
                                network=network,
                                block_signer=block_signers.block_signers[i],
                                behaviour=behaviour,
                                launch_mode=0)
            network.register_node(keyless_node)
            nodes.append(keyless_node)

        for node in nodes:
            if not node.isAlive():
                node.start()

        signal.signal(signal.SIGINT, signal_handler)
        
Initializer()
