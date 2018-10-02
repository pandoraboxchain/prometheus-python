import unittest
import os

from crypto.private import Private
from transaction.stake_transaction import StakeHoldTransaction, StakeReleaseTransaction, PenaltyTransaction

class TestTransaction(unittest.TestCase):

    def test_pack_parse_stakehold_transaction(self):
        private = Private.generate()
        original = StakeHoldTransaction()
        original.amount = 1000
        original.pubkey = Private.publickey(private)
        original.signature = Private.sign(original.get_hash(), private)

        raw = original.pack()
        restored = StakeHoldTransaction()
        restored.parse(raw)

        self.assertEqual(original.get_hash(), restored.get_hash())   

    def test_pack_parse_penalty_transaction(self):
        original = PenaltyTransaction()
        original.violator_pubkey = Private.publickey(Private.generate())
        original.conflicts = [os.urandom(32), os.urandom(32), os.urandom(32)]
        original.signature = Private.sign(original.get_hash(), Private.generate())

        raw = original.pack()
        restored = PenaltyTransaction()
        restored.parse(raw)

        self.assertEqual(original.get_hash(), restored.get_hash()) 

    def test_pack_parse_stakerelease_transaction(self):
        private = Private.generate()
        original = StakeReleaseTransaction()
        original.pubkey = Private.publickey(private)
        original.signature = Private.sign(original.get_hash(), Private.generate())

        raw = original.pack()
        restored = StakeReleaseTransaction()
        restored.parse(raw)

        self.assertEqual(original.get_hash(), restored.get_hash())        
