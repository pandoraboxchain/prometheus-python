import unittest

from core.node.node import Node
from core.chain.node_api import NodeApi
from core.chain.block_signers import BlockSigners
from core.chain.validators import Validators
from core.chain.epoch import Epoch
from core.chain.behaviour import Behaviour
from core.tools.time import Time


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
        behavior = Behaviour()
        validators = Validators()
        node_id = 14
        node = Node(genesis_creation_time=1,
                    node_index=node_id,
                    network=network,
                    validators=validators,
                    block_signer=private_keys[node_id],
                    behaviour=behavior,
                    launch_mode=0)
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
        validators.validators = Validators.get_from_file(Validators())
        validators.signers_order = [0] + [1] * Epoch.get_duration()
        validators.randomizers_order = [0] * Epoch.get_duration()

        network = NodeApi()
        behavior = Behaviour()
        node0 = Node(genesis_creation_time=1,
                     node_index=0,
                     network=network,
                     block_signer=private_keys[0],
                     validators=validators,
                     behaviour=behavior,
                     launch_mode=0)
        network.register_node(node0)

        node1 = Node(genesis_creation_time=1,
                     node_index=1,
                     network=network,
                     block_signer=private_keys[1],
                     validators=validators,
                     behaviour=behavior,
                     launch_mode=0)
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

        


