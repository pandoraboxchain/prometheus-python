import unittest
import os
import logging

from chain.node import Node
from chain.node_api import NodeApi
from chain.behaviour import Behaviour
from chain.block_signers import BlockSigners
from tests.test_chain_generator import TestChainGenerator
from tools.time import Time
from crypto.private import Private


class TestNode(unittest.TestCase):
    def test_time_advancer(self):

        Time.use_test_time()

        Time.set_current_time(7)
        self.assertEqual(Time.get_current_time(), 7)
        
        Time.advance_block_time()
        self.assertEqual(Time.get_current_time(), 11)

    def test_block_sign(self):
        Time.use_test_time()
        Time.set_current_time(1)

        private_keys = BlockSigners()
        private_keys = private_keys.block_signers

        behaviour = Behaviour()
        logger = logging.getLogger('')
        network = NodeApi()
        node_id = 14
        node = Node(1, node_id, network, logger, private_keys[node_id], behaviour)
        network.register_node(node)

        dag = node.dag

        node.step()
        Time.advance_block_time()
        self.assertEqual(len(dag.blocks_by_hash), 1)

        node.step()
        self.assertEqual(len(dag.blocks_by_hash), 2)


        


