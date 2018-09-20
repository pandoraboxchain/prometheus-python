import unittest
import os

from chain.node import Node
from chain.node_api import NodeApi
from chain.behaviour import Behaviour
from chain.block_signers import BlockSigners
from chain.validators import Validators
from chain.epoch import Epoch
from tests.test_chain_generator import TestChainGenerator
from tools.time import Time
from crypto.private import Private


class TestNode(unittest.TestCase):

    def test_time_advancer(self):

        Time.use_test_time()

        Time.set_current_time(7)
        self.assertEqual(Time.get_current_time(), 7)
        
        Time.advance_to_next_timeslot()
        self.assertEqual(Time.get_current_time(), 11)

    def test_block_sign(self):
        Time.use_test_time()
        Time.set_current_time(1)

        private_keys = BlockSigners()
        private_keys = private_keys.block_signers

        network = NodeApi()
        node_id = 14
        node = Node(genesis_creation_time=1,
                    node_id=node_id,
                    network=network,
                    block_signer=private_keys[node_id])
        network.register_node(node)

        dag = node.dag

        node.step()
        Time.advance_to_next_timeslot()
        self.assertEqual(len(dag.blocks_by_hash), 1)

        node.step()
        self.assertEqual(len(dag.blocks_by_hash), 2)

    def test_broadcast_public_key(self):
        Time.use_test_time()
        Time.set_current_time(1)

        private_keys = BlockSigners()
        private_keys = private_keys.block_signers

        validators = Validators()
        validators.validators = Validators.read_genesis_validators_from_file()
        validators.signers_order = [0] + [1] * Epoch.get_duration() 
        validators.randomizers_order = [0] * Epoch.get_duration()

        network = NodeApi()
        node0 = Node(genesis_creation_time=1,
                     node_id=0,
                     network=network,
                     block_signer=private_keys[0],
                     validators=validators)
        network.register_node(node0)

        node1 = Node(genesis_creation_time=1,
                     node_id=1,
                     network=network,
                     block_signer=private_keys[1],
                     validators=validators)
        network.register_node(node1)

        Time.advance_to_next_timeslot()
        node0.step()

        tops = node1.dag.get_top_blocks_hashes()
        pubkeys = node1.epoch.get_public_keys_for_epoch(tops[0])
        self.assertEqual(len(pubkeys), 0)

        Time.advance_to_next_timeslot()
        node1.step()

        tops = node1.dag.get_top_blocks_hashes()
        pubkeys = node1.epoch.get_public_keys_for_epoch(tops[0])

        self.assertEqual(len(pubkeys), 1)

        


