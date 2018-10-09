import unittest
import os
from transaction.secret_sharing_transactions import SplitRandomTransaction
from transaction.commit_transactions import CommitRandomTransaction, RevealRandomTransaction
from transaction.transaction_parser import TransactionParser
from transaction.payment_transaction import PaymentTransaction
from hashlib import sha256
from crypto.private import Private
from crypto.keys import Keys


class TestTransaction(unittest.TestCase):

    def test_pack_parse_commit_transaction(self):
        for i in range(10):
            dummy_private = Private.generate()
            original = CommitRandomTransaction()
            original.rand = Private.encrypt(os.urandom(32), dummy_private)
            original.pubkey_index = i
            original.signature = Private.sign(original.get_signing_hash(b"epoch_hash"), dummy_private)

            raw = original.pack()
            restored = CommitRandomTransaction()
            restored.parse(raw)

            self.assertEqual(TransactionParser.pack(original), TransactionParser.pack(restored))        
            self.assertEqual(original.get_hash(), restored.get_hash())
            self.assertEqual(original.get_signing_hash(b"epoch_hash"), restored.get_signing_hash(b"epoch_hash"))

    def test_pack_parse_reveal_transaction(self):
        for _ in range(10):
            dummy_private = Private.generate()

            original = RevealRandomTransaction()
            original.commit_hash = sha256(b"previous_transaction").digest()
            original.key = Keys.to_bytes(dummy_private)

            raw = original.pack()
            restored = RevealRandomTransaction()
            restored.parse(raw)

            self.assertEqual(TransactionParser.pack(original), TransactionParser.pack(restored))        
            self.assertEqual(original.get_hash(), restored.get_hash())

    def test_split_pack_unpack(self):
        dummy_private = Private.generate()

        original = SplitRandomTransaction()
        original.pieces = [os.urandom(128), os.urandom(127), os.urandom(128)]
        original.signature = Private.sign(original.get_signing_hash(b"epoch_hash"), dummy_private)

        raw = original.pack()
        restored = SplitRandomTransaction()
        restored.parse(raw)

        self.assertEqual(original.get_hash(), restored.get_hash())        
        self.assertEqual(original.get_signing_hash(b"epoch_hash"), restored.get_signing_hash(b"epoch_hash"))

    def test_payment_pack_unpack(self):
        dummy_private = Private.generate()
        original = PaymentTransaction()
        original.from_tx = os.urandom(32)
        original.amount = 123
        original.to = os.urandom(32)
        original.pubkey = Private.publickey(dummy_private)
        original.signature = Private.sign(original.get_hash(), dummy_private)

        raw = original.pack()
        restored = PaymentTransaction()
        restored.parse(raw)

        self.assertEqual(original.get_hash(), restored.get_hash())       
     



