import unittest
import os
from chain.block import Block
from transaction.transaction import CommitRandomTransaction, Type
from crypto.enc_random import enc_part_random
from Crypto.Hash import SHA256

class TestBlock(unittest.TestCase):

    def test_pack_parse(self):
        original_block = Block()
        original_block.timestamp = 2344
        original_block.prev_hashes = [SHA256.new(b"323423").digest(), SHA256.new(b"0").digest()]

        commit_tx = CommitRandomTransaction()
        data, _ = enc_part_random(SHA256.new(b"era_hash").digest())
        commit_tx.rand = data
        commit_tx.pubkey = os.urandom(216)
        commit_tx.signature = int.from_bytes(os.urandom(128), byteorder='big')

        original_block.system_txs = [commit_tx]

        raw = original_block.pack()
        restored = Block()
        restored.parse(raw)

        self.assertEqual(original_block.get_hash().digest(), restored.get_hash().digest())
