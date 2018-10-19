import unittest

from node.node import Node
from node.node_api import NodeApi
from node.block_signers import BlockSigners
from node.validators import Validators
from chain.epoch import Epoch
from tests.test_chain_generator import TestChainGenerator
from tools.time import Time

from chain.params import BLOCK_TIME, ROUND_DURATION


class TestNode(unittest.TestCase):

    def test_time_advancer(self):

        Time.use_test_time()

        time_value = 7  # for example
        Time.set_current_time(time_value)
        self.assertEqual(Time.get_current_time(), time_value)
        
        Time.advance_to_next_timeslot()
        self.assertEqual(Time.get_current_time(), time_value + BLOCK_TIME)

    def test_block_sign(self):
        Time.use_test_time()
        Time.set_current_time(1)

        private_keys = BlockSigners()
        private_keys = private_keys.block_signers

        validators = Validators()
        validators.validators = Validators.read_genesis_validators_from_file()
        validators.signers_order = [0] + [1] * Epoch.get_duration()
        validators.randomizers_order = [0] * Epoch.get_duration()

        network = NodeApi()
        node_id = 0
        node = Node(genesis_creation_time=1,
                    node_id=node_id,
                    network=network,
                    block_signer=private_keys[node_id],
                    validators=validators)
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

    def test_allowed_signers_by_block_number(self):
        Time.use_test_time()
        Time.set_current_time(1)

        private_keys = BlockSigners()
        private_keys = private_keys.block_signers

        validators = Validators()
        validators.validators = Validators.read_genesis_validators_from_file()
        validators.signers_order = [0, 1, 2] * 10
        validators.randomizers_order = [0] * Epoch.get_duration()

        validators_pubkeys = [validator.public_key for validator in validators.validators]

        network = NodeApi()
        node0 = Node(genesis_creation_time=1,
                     node_id=0,
                     network=network,
                     block_signer=private_keys[0],
                     validators=validators)
        network.register_node(node0)
                    
        allowed_signers = node0.get_allowed_signers_for_block_number(3)
        self.assertEqual(allowed_signers[0], validators_pubkeys[2]) #simple case

        # generate two branches resulting in two epoch_hashes
        node0.dag = TestChainGenerator.generate_two_chains(ROUND_DURATION * 6 + 1)
        tops = node0.dag.get_top_hashes()

        # assign pseudo generated list of validators to cache for each epoch

        # same validators
        node0.permissions.epoch_validators[tops[0]] = validators.validators
        # different order
        node0.permissions.signers_indexes[tops[0]] = [1,1,1] * 10

        # same validators
        node0.permissions.epoch_validators[tops[1]] = validators.validators
        # different order
        node0.permissions.signers_indexes[tops[1]] = [5,5,5] * 10

        allowed_signers = node0.get_allowed_signers_for_block_number(ROUND_DURATION * 6 + 2)
        self.assertEqual(len(allowed_signers), 2)
        self.assertIn(validators_pubkeys[1], allowed_signers)
        self.assertIn(validators_pubkeys[5], allowed_signers)


        

        

        


