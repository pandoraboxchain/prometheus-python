import asyncio
import logging
import importlib
import datetime
import random


from node.node import Node
from node.network import Network
from node.block_signers import BlockSigners
from node.behaviour import Behaviour
from node.stats import Stats

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


def show_node_stats(node):
    Stats.gather(node)


class Initializer:

    # on initializer start will assert init params
    @staticmethod
    def params_validate():
        #  GENESIS_VALIDATORS_COUNT - initial number ov validators(min 20)
        #  BLOCK_TIME - steps/seconds per block                   (min 2, sable 4)
        #  ROUND_DURATION - blocks per round                      (FINAL = ROUND_DURATION +1)
        #  EPOCH - [PUBLIC, COMMIT, SECRETSHARE, REVEAL, PRIVATE, FINAL]
        print('GENESIS_VALIDATORS_COUNT : ' + str(GENESIS_VALIDATORS_COUNT))
        print('BLOCK_TIME               : ' + str(BLOCK_TIME))
        print('ROUND_DURATION           : ' + str(ROUND_DURATION))
        # check minimum values
        assert (GENESIS_VALIDATORS_COUNT >= 19), 'Minimum initial validators is 19 ((3 blocks per round)+1, 6 rounds)'
        assert (BLOCK_TIME >= 2), 'Block time minimum value is 2, please increase block time'
        assert (ROUND_DURATION >= 3), 'Minimum value is 3 blocks per round for 20 validators'
        # check values in proportion
        # ROUND_DURATION on GENESIS_VALIDATORS_COUNT
        assert (
        GENESIS_VALIDATORS_COUNT >= ROUND_DURATION * 6 + 1), 'Wrong validators count on blocks per round proportion.' \
                                                             'Validators count must be >= round_duration * 6 + 1'

    def __init__(self):
        self.node_to_visualize_after_exit = 0
        self.params_validate()
        self.discrete_mode = False
        self.malicious_validators_count = 0  # GENESIS_VALIDATORS_COUNT / 2 - 1
        # set up logging to file - see previous section for more details
        self.logger = logging.basicConfig(level=logging.DEBUG,
                                          format='%(asctime)s %(levelname)-6s %(name)-6s %(message)s')

        if self.discrete_mode:
            Time.use_test_time()
            Time.set_current_time(BLOCK_TIME)
        else:
            Time.set_current_time(int(datetime.datetime.now().timestamp()))
        self.genesis_creation_time = Time.get_current_time() - BLOCK_TIME  # so we start right from the first block

        self.private_keys = BlockSigners()
        self.network = Network()
        self.nodes = []
        self.tasks = []
        try:
            # -------------------------------------
            # main init section
            # -------------------------------------
            self.launch()
            # add some extra nodes
            #self.add_node(10)
            # -------------------------------------

            if self.discrete_mode:
                should_continue = True
                terminated_nodes_count = 0
                while should_continue:
                    initial_node_count = len(self.nodes) - 1 # one node less because of announcer
                    for node in self.nodes:
                        try:
                            if not node.terminated:
                                node.step()
                        except AssertionError:
                            print("Node", node.node_id, "crashed")
                            self.network.unregister_node(node)
                            node.terminated = True
                            terminated_nodes_count += 1
                            if terminated_nodes_count == initial_node_count:
                                print("No alive nodes left. Terminating")
                                should_continue = False
                                break
                        
                    Time.advance_time(1)

                    # add some nodes on defined time
                    # will be possible after syncronization mechanism will be implemented)
                    # if Time.get_current_time() == 40:
                    #    self.add_node(1)
            else:
                self.tasks = [node.run() for node in self.nodes]
                loop = asyncio.get_event_loop()
                loop.run_until_complete(asyncio.gather(*self.tasks))
                loop.close()
        
        finally:
            if self.node_to_visualize_after_exit:
                save_dag_to_graphviz(self.node_to_visualize_after_exit.dag)
                # show_node_stats(self.node_to_visualize_after_exit)

    def launch(self):
        logger = logging.getLogger("Announce")
        announcer = AnnouncerNode(self.genesis_creation_time, logger)
        self.nodes.append(announcer)

        for i in range(0, GENESIS_VALIDATORS_COUNT):
            behaviour = self.generate_behaviour(i)
            # if i==7:
            #     behaviour.malicious_wrong_signature = True
            # behavior for gossip emulation (create block but not broadcast)
            # if i == 3:
            #    behaviour.transport_cancel_block_broadcast = True
            # uncomment the following line to enable logging only on specific node
            # if i != 13: logger.setLevel(logging.CRITICAL)
            logger = logging.getLogger("Node " + str(i))
            node = Node(genesis_creation_time=self.genesis_creation_time,
                        node_id=i,
                        network=self.network,
                        behaviour=behaviour,
                        block_signer=self.private_keys.block_signers[i],
                        logger=logger)

            if i == self.node_to_visualize_after_exit:
                self.node_to_visualize_after_exit = node
            self.network.register_node(node)
            self.nodes.append(node)

    def add_node(self, count):
        for i in range(GENESIS_VALIDATORS_COUNT, GENESIS_VALIDATORS_COUNT+count):
            behaviour = Behaviour()
            behaviour.wants_to_hold_stake = True
            behaviour.epoch_to_release_stake = 2
            logger = logging.getLogger("Node " + str(i))
            keyless_node = Node(genesis_creation_time=self.genesis_creation_time,
                                node_id=i,
                                network=self.network,
                                logger=logger)
            self.network.register_node(keyless_node)
            self.tasks.append(keyless_node.run())

    def generate_behaviour(self, i=-1):
        randgen = random.SystemRandom() 
        behaviour = Behaviour()
        if self.malicious_validators_count:
            behaviour = Behaviour()
            malicious_flags = behaviour.get_malicious_flags_names()
            chosen_flag_name = randgen.choice(malicious_flags)
            if i != -1: print("Node", i, "set", chosen_flag_name)
            setattr(behaviour,chosen_flag_name, True)
            self.malicious_validators_count -= 1
        
        return behaviour

Initializer()
