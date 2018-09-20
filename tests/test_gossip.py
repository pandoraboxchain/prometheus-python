import unittest

from chain.behaviour import Behaviour
from chain.block_factory import BlockFactory
from chain.block_signers import BlockSigners
from chain.epoch import Epoch
from chain.node import Node
from chain.node_api import NodeApi
from chain.validators import Validators
from crypto.keys import Keys
from crypto.private import Private
from tools.time import Time
from transaction.gossip_transaction import PositiveGossipTransaction, NegativeGossipTransaction


class TestGossip(unittest.TestCase):

    def test_parse_pack_gossip_positive(self):
        private = Private.generate()
        original = PositiveGossipTransaction()
        original.node_public_key = Keys.to_bytes(private.publickey())
        original.timestamp = Time.get_current_time()

        block = BlockFactory.create_block_with_timestamp([], timestamp=original.timestamp)
        original.block = BlockFactory.sign_block(block, private)
        original.signature = private.sign(original.get_hash(), 0)[0]

        raw = original.pack()
        restored = PositiveGossipTransaction()
        restored.parse(raw)

        self.assertEqual(original.get_hash(), restored.get_hash())

    def test_parse_pack_gossip_negative(self):
        private = Private.generate()
        original = NegativeGossipTransaction()
        original.node_public_key = Keys.to_bytes(private.publickey())
        original.timestamp = Time.get_current_time()
        original.number_of_block = 47
        original.signature = private.sign(original.get_hash(), 0)[0]

        raw = original.pack()
        restored = NegativeGossipTransaction()
        restored.parse(raw)

        self.assertEqual(original.get_hash(), restored.get_hash())

    def test_send_negative_gossip(self):
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
                     validators=validators,
                     behaviour=Behaviour())
        network.register_node(node0)

        behavior = Behaviour()
        behavior.malicious_skip_block_receive = True
        node1 = Node(genesis_creation_time=1,
                     node_id=1,
                     network=network,
                     block_signer=private_keys[1],
                     validators=validators,
                     behaviour=behavior)
        network.register_node(node1)

        Time.advance_to_next_timeslot()
        node0.step()
        # ensure that node 0 create and send block
        self.assertEqual(len(node0.dag.blocks_by_number), 2)

        node1.step()
        # ensure that node 1 do not receive block
        self.assertEqual(len(node1.dag.blocks_by_number), 1)

        Time.advance_to_next_timeslot()
        node0.step()
        node1.step()
        # ensure that node 1 send negative gossip transaction
        self.assertEqual(len(node0.mempool.gossips), 1)
