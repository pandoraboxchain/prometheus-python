import asyncio
import logging
import importlib
import datetime

from node.node import Node
from node.node_api import NodeApi
from node.block_signers import BlockSigners
from node.behaviour import Behaviour

from tools.announcer_node import AnnouncerNode
from tools.time import Time

from chain.params import GENESIS_VALIDATORS_COUNT, \
                         BLOCK_TIME, \
                         ROUND_DURATION


# you can set node to visualize its DAG as soon as Ctrl-C pressed
def save_dag_to_graphviz(dag_to_visualize):
    graphviz_import = importlib.util.find_spec("graphviz")
    graphviz_lib_installed = graphviz_import is not None
    if graphviz_lib_installed:
        from visualization.dag_visualizer import DagVisualizer
        DagVisualizer.visualize(dag_to_visualize)


# on initializer start will assert init params
def params_validate():

    #  GENESIS_VALIDATORS_COUNT - initial number ov validators(min 20)
    #  BLOCK_TIME - steps/seconds per block                   (min 2, sable 4)
    #  ROUND_DURATION - blocks per round                      (FINAL = ROUND_DURATION +1)
    #  EPOCH - [PUBLIC, COMMIT, SECRETSHARE, REVEAL, PRIVATE, FINAL]
    print('GENESIS_VALIDATORS_COUNT : ' + str(GENESIS_VALIDATORS_COUNT))
    print('BLOCK_TIME               : ' + str(BLOCK_TIME))
    print('ROUND_DURATION           : ' + str(ROUND_DURATION))
    # check minimum values
    assert (GENESIS_VALIDATORS_COUNT >= 20), 'Minimum initial validators is 19 ((3 blocks per round)+1, 6 rounds)'
    assert (BLOCK_TIME >= 2), 'Block time minimum value is 2, please increase block time'
    assert (ROUND_DURATION >= 3), 'Minimum value is 3 blocks per round for 20 validators'
    # check values in proportion
    # ROUND_DURATION on GENESIS_VALIDATORS_COUNT
    assert (GENESIS_VALIDATORS_COUNT >= ROUND_DURATION*6+1), 'Wrong validators count on blocks per round proportion.' \
                                                             'Validators count must be >= round_duration * 6 + 1'


class Initializer:

    def __init__(self):
        node_to_visualize_after_exit = None
        params_validate()
        try:
            # set up logging to file - see previous section for more details
            logging.basicConfig(level=logging.DEBUG,
                                format='%(asctime)s %(levelname)-6s %(name)-6s %(message)s')

            discrete_mode = True

            if discrete_mode:
                Time.use_test_time()
                Time.set_current_time(BLOCK_TIME)
            else:
                Time.set_current_time(int(datetime.datetime.now().timestamp()))

            genesis_creation_time = Time.get_current_time() - BLOCK_TIME  # so we start right from the first block

            private_keys = BlockSigners()

            network = NodeApi()

            nodes = []

            logger = logging.getLogger("Announce")
            announcer = AnnouncerNode(genesis_creation_time, logger)
            nodes.append(announcer)
            
            for i in range(0, GENESIS_VALIDATORS_COUNT):
                behaviour = Behaviour()

                # if i==7:
                #     behaviour.malicious_wrong_signature = True

                # behavior for gossip emulation (create block but not broadcast)
                # if i == 3:
                #    behaviour.transport_cancel_block_broadcast = True

                logger = logging.getLogger("Node " + str(i))
                # uncomment the following line to enable logging only on specific node
                # if i != 13: logger.setLevel(logging.CRITICAL)

                node = Node(genesis_creation_time=genesis_creation_time,
                            node_id=i,
                            network=network,
                            behaviour=behaviour,
                            block_signer=private_keys.block_signers[i],
                            logger=logger)

                if i == 0:
                    node_to_visualize_after_exit = node
                network.register_node(node)
                nodes.append(node)

            # for i in range(19, 20):
            #     behaviour = Behaviour()
            #     behaviour.wants_to_hold_stake = True
            #     behaviour.epoch_to_release_stake = 2
            #     logger = logging.getLogger("Node " + str(i))
            #     keyless_node = Node(genesis_creation_time=genesis_creation_time,
            #                         node_id=i,
            #                         network=network,
            #                         block_signer=private_keys.block_signers[i],
            #                         logger=logger)
            #     network.register_node(keyless_node)
            #     tasks.append(keyless_node.run())
            if discrete_mode:
                while True:
                    for node in nodes:
                        node.step()
                    Time.advance_time(1)
            else:
                tasks = [node.run() for node in nodes] 
                loop = asyncio.get_event_loop()
                loop.run_until_complete(asyncio.gather(*tasks))       
                loop.close()
        
        finally:
            if node_to_visualize_after_exit:
                save_dag_to_graphviz(node_to_visualize_after_exit.dag)

Initializer()
