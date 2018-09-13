import unittest
import os
from tools.time import Time
from crypto.private import Private
from crypto.keys import Keys
from gossip.gossip import PositiveGossip, NegativeGossip
from chain.block_factory import BlockFactory


class TestGossip(unittest.TestCase):

    def test_parse_pack_gossip_positive(self):
        private = Private.generate()
        original = PositiveGossip()
        original.node_public_key = Keys.to_bytes(private.publickey())
        original.timestamp = Time.get_current_time()

        block = BlockFactory.create_block_with_timestamp([], timestamp=original.timestamp)
        original.block = BlockFactory.sign_block(block, private)
        original.signature = private.sign(original.get_hash(), 0)[0]

        raw = original.pack()
        restored = PositiveGossip()
        restored.parse(raw)

        self.assertEqual(original.get_hash(), restored.get_hash())

    def test_parse_pack_gossip_negative(self):
        private = Private.generate()
        original = NegativeGossip()
        original.node_public_key = Keys.to_bytes(private.publickey())
        original.timestamp = Time.get_current_time()
        original.number_of_block = 47
        original.signature = private.sign(original.get_hash(), 0)[0]

        raw = original.pack()
        restored = NegativeGossip()
        restored.parse(raw)

        self.assertEqual(original.get_hash(), restored.get_hash())


