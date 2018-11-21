import logging
import unittest

from chain.params import ROUND_DURATION
from crypto.private import Private
from node.behaviour import Behaviour
from node.block_signers import BlockSigner
from node.node import Node
from tools.time import Time


class TestHelper(unittest.TestCase):

    def __init__(self, network):
        super().__init__()
        self.network = network

    def generate_nodes(self, block_signers, count):
        behaviour = Behaviour()
        for i in range(0, count):
            logger = logging.getLogger("Node " + str(i))
            node = Node(genesis_creation_time=1,
                        node_id=i,
                        network=self.network,
                        behaviour=behaviour,
                        block_signer=block_signers[i],
                        logger=logger)
            self.network.register_node(node)

    def add_stakeholders(self, count):
        behaviour = Behaviour()
        behaviour.wants_to_hold_stake = True
        for i in range(0, count):
            index = len(self.network.nodes)
            logger = logging.getLogger("Node " + str(index))
            node = Node(genesis_creation_time=1,
                        block_signer=BlockSigner(Private.generate()),
                        node_id=index,
                        network=self.network,
                        behaviour=behaviour,
                        logger=logger)
            self.network.register_node(node)

    def perform_block_steps(self, timeslote_count):
        for t in range(0, timeslote_count):  # by timeslots
            Time.advance_to_next_timeslot()
            for s in range(0, ROUND_DURATION):  # by steps
                for node in self.network.nodes:  # by nodes
                    node.step()

    def perform_in_block_single_step(self, count):
        for s in range(0, count):
            for node in self.network.nodes:  # by nodes
                node.step()

    def list_validator(self, node_list, functions, value):
        """
            Method provide check of registered for network nodes (or custom nodes list to check)
            and perform assertTrue for all nodes in nodes_list for specific parameter by value
            :param node_list: list of nodes for validation
            :param functions: see list of params in method or add necessary
            :param value: value of condition
            :return: nothing (provide assertation)
        """
        for node in node_list:
            if 'mempool.gossips.length' in functions:
                self.assertEqual(len(node.mempool.gossips), value)
            if 'dag.blocks_by_number.length' in functions:
                self.assertEqual(len(node.dag.blocks_by_number), value)
            if 'dag.transactions_by_hash.length' in functions:
                self.assertEqual(len(node.dag.transactions_by_hash), value)
            if 'permissions.epoch_validators.length' in functions:
                validators_list = node.permissions.epoch_validators
                validators_list = next(iter(validators_list.values()))
                self.assertEqual(len(validators_list), value)
            if 'permissions.epoch_validators.epoch0.length' in functions:
                validators_list = node.permissions.epoch_validators
                validators_list = next(iter(validators_list.values()))
                self.assertEqual(len(validators_list), value)
            if 'permissions.epoch_validators.epoch1.length' in functions:
                validators_list = node.permissions.epoch_validators
                validators_list = next(iter(validators_list.values()))
                self.assertEqual(len(validators_list), value)