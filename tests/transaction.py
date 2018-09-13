import unittest
import os
from chain.block import Block
from transaction.secret_sharing_transactions import SplitRandomTransaction
from transaction.commit_transactions import CommitRandomTransaction, RevealRandomTransaction
from transaction.transaction_parser import TransactionParser

from crypto.enc_random import enc_part_random
from Crypto.Hash import SHA256
from crypto.private import Private
from crypto.keys import Keys

class TestTransaction(unittest.TestCase):

    def test_pack_parse_commit_transaction(self):
        for _ in range(10):
            dummy_private = Private.generate()
            original = CommitRandomTransaction()
            original.rand = dummy_private.encrypt(os.urandom(32), 0)[0]
            original.pubkey = Keys.to_bytes(dummy_private.publickey())
            original.signature = int.from_bytes(os.urandom(128), byteorder='big')

            raw = original.pack()
            restored = CommitRandomTransaction()
            restored.parse(raw)

            self.assertEqual(TransactionParser.pack(original), TransactionParser.pack(restored))        
            self.assertEqual(original.get_reference_hash(), restored.get_reference_hash())

    def test_pack_parse_reveal_transaction(self):
        for _ in range(10):
            dummy_private = Private.generate()

            original = RevealRandomTransaction()
            original.commit_hash = SHA256.new(b"previous_transaction").digest()
            original.key = Keys.to_bytes(dummy_private)

            raw = original.pack()
            restored = RevealRandomTransaction()
            restored.parse(raw)

            self.assertEqual(TransactionParser.pack(original), TransactionParser.pack(restored))        
            self.assertEqual(original.get_hash(), restored.get_hash())        

    def test_split_pack_unpack(self):
        original = SplitRandomTransaction()
        original.pieces = [os.urandom(128), os.urandom(127), os.urandom(128)]
        original.signature = int.from_bytes(os.urandom(128), byteorder='big')

        raw = original.pack()
        restored = SplitRandomTransaction()
        restored.parse(raw)

        self.assertEqual(original.get_reference_hash(), restored.get_reference_hash())        
        self.assertEqual(original.get_signing_hash(b"epoch_hash"), restored.get_signing_hash(b"epoch_hash"))        



