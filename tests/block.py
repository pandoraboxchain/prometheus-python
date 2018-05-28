import unittest
from chain.block import Block
from Crypto.Hash import SHA256

class TestBlock(unittest.TestCase):

    def test_pack_parse(self):
        original_block = Block()
        original_block.timestamp = 2344
        original_block.prev_hashes = [SHA256.new(b"323423").digest(), SHA256.new(b"0").digest()]
        original_block.randoms = [1,2,3,4,5]

        raw = original_block.pack()
        restored = Block()
        restored.parse(raw)

        self.assertEqual(original_block.get_hash().digest(), restored.get_hash().digest())
