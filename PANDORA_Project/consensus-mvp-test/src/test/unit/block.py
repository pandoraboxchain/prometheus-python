import os
import unittest

from Crypto.Hash import SHA256
from core.chain.block import Block
from core.crypto.keys import Keys
from core.crypto.private import Private

from core.transaction.secret_sharing_transactions import SplitRandomTransaction, PrivateKeyTransaction


class TestBlock(unittest.TestCase):

    def test_pack_parse(self):
        original_block = Block()
        original_block.timestamp = 2344
        original_block.prev_hashes = [SHA256.new(b"323423").digest(), SHA256.new(b"0").digest()]

        tx = SplitRandomTransaction()
        tx.pieces = [os.urandom(128), os.urandom(128), os.urandom(128)]
        tx.signature = int.from_bytes(os.urandom(128), byteorder='big')

        pktx = PrivateKeyTransaction()
        pktx.key = Keys.to_bytes(Private.generate())

        original_block.system_txs = [tx, pktx]

        raw = original_block.pack()
        restored = Block()
        restored.parse(raw)

        self.assertEqual(original_block.get_hash(), restored.get_hash())
        self.assertEqual(tx.get_reference_hash(), restored.system_txs[0].get_reference_hash())
        self.assertEqual(pktx.get_hash(), restored.system_txs[1].get_hash())


