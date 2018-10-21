import unittest
import os
from chain.block import Block
from transaction.secret_sharing_transactions import SplitRandomTransaction, PrivateKeyTransaction
from transaction.payment_transaction import PaymentTransaction
from crypto.private import Private
from crypto.keys import Keys

from hashlib import sha256


class TestBlock(unittest.TestCase):

    def test_pack_parse(self):
        original_block = Block()
        original_block.timestamp = 2344
        original_block.prev_hashes = [sha256(b"323423").digest(), sha256(b"0").digest()]

        tx = SplitRandomTransaction()
        tx.pieces = [os.urandom(128), os.urandom(128), os.urandom(128)]
        tx.pubkey_index = 0
        tx.signature = Private.sign(tx.get_signing_hash(b"epoch_hash"), Private.generate())

        pktx = PrivateKeyTransaction()
        pktx.key = Keys.to_bytes(Private.generate())

        original_block.system_txs = [tx, pktx]

        payment = PaymentTransaction()
        payment.input = b'0' * 32
        payment.number = 0
        payment.outputs = [os.urandom(32)]
        payment.amounts = [15]

        original_block.payment_txs = [payment]

        raw = original_block.pack()
        restored = Block()
        restored.parse(raw)

        self.assertEqual(original_block.get_hash(), restored.get_hash())
        self.assertEqual(tx.get_hash(), restored.system_txs[0].get_hash())
        self.assertEqual(pktx.get_hash(), restored.system_txs[1].get_hash())

