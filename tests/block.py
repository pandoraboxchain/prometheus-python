import unittest
#from ...chain.block import Block #TODO fix that import
from Crypto.Hash import SHA256

class TestBlock(unittest.TestCase):

    def test_pack_parse(self):
        original_block = Block()
        original_block.timestamp = 2344
        original_block.prev_hashes = [SHA256.new(b"323423").digest(), SHA256.new(b"0").digest()]
        original_block.randoms = [1,2,3,4,5]

        raw = original_block.pack()
        restored = Block()
        restored.set_raw_data(raw)
        restored.parse()

        self.assertEqual(original_block, restored)
