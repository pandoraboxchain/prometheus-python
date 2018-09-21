import unittest

from node.behaviour import Behaviour
from chain.block_factory import BlockFactory
from chain.epoch import Epoch
from node.block_signers import BlockSigners
from node.node import Node
from node.node_api import NodeApi
from node.validators import Validators
from crypto.keys import Keys
from crypto.private import Private
from tools.time import Time
from transaction.gossip_transaction import PositiveGossipTransaction, NegativeGossipTransaction


class TestGossip(unittest.TestCase):

    def test_parse_pack_gossip_positive(self):
        private = Private.generate()
        original = PositiveGossipTransaction()
        original.pubkey = Keys.to_bytes(private.publickey())
        original.timestamp = Time.get_current_time()

        block = BlockFactory.create_block_with_timestamp([], timestamp=original.timestamp)
        original.block = BlockFactory.sign_block(block, private)
        original.signature = Private.sign(original.get_hash(), private)

        raw = original.pack()
        restored = PositiveGossipTransaction()
        restored.parse(raw)

        self.assertEqual(original.get_hash(), restored.get_hash())

    def test_parse_pack_gossip_negative(self):
        private = Private.generate()
        original = NegativeGossipTransaction()
        original.pubkey = Keys.to_bytes(private.publickey())
        original.timestamp = Time.get_current_time()
        original.number_of_block = 47
        original.signature = Private.sign(original.get_hash(), private)

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
        behavior = Behaviour()
        behavior.malicious_skip_block = True
        node0 = Node(genesis_creation_time=1,
                     node_id=0,
                     network=network,
                     block_signer=private_keys[0],
                     validators=validators,
                     behaviour=behavior)
        network.register_node(node0)

        node1 = Node(genesis_creation_time=1,
                     node_id=1,
                     network=network,
                     block_signer=private_keys[1],
                     validators=validators,
                     behaviour=Behaviour())
        network.register_node(node1)

        Time.advance_to_next_timeslot()
        node0.step()
        self.assertEqual(len(node0.dag.blocks_by_number), 1)  # ensure that block skipped by node0
        node1.step()
        self.assertEqual(len(node0.dag.blocks_by_number), 1)  # ensure that block not received by node1

        Time.advance_to_next_timeslot()
        # on next step node0 broadcast negative gossip
        node0.step()
        # and not include it to (node0) self.mempool
        self.assertEqual(len(node0.mempool.gossips), 0)
        # assume that negative gossip broadcasted and placed to node1 mempool
        self.assertEqual(len(node1.mempool.gossips), 1)

        # on next step node 1 will send negative gossip
        # node1 MUST create and sign block which contain negative gossip and broadcast it
        node1.step()

        # verify that node1 make block broadcast
        self.assertEqual(len(node1.dag.blocks_by_number), 2)
        # verify that node0 receive new block
        self.assertEqual(len(node0.dag.blocks_by_number), 2)
        # verify that negative gossip transaction is in block
        last_block = node0.dag.blocks_by_number[2]
        signed_block = last_block[0]
        block = signed_block.block
        system_txs = block.system_txs
        self.assertTrue(NegativeGossipTransaction.__class__, system_txs[3].__class__)
