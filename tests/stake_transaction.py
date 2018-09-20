import unittest
import os
from transaction.stake_transaction import StakeHoldTransaction, StakeReleaseTransaction, PenaltyTransaction
from Crypto.Hash import SHA256

class TestTransaction(unittest.TestCase):

    def test_pack_parse_stakehold_transaction(self):
        original = StakeHoldTransaction()
        original.amount = 1000
        original.pubkey = os.urandom(216)
        original.signature = int.from_bytes(os.urandom(128), byteorder='big')

        raw = original.pack()
        restored = StakeHoldTransaction()
        restored.parse(raw)

        self.assertEqual(original.get_hash(), restored.get_hash())   

    def test_pack_parse_penalty_transaction(self):
        original = PenaltyTransaction()
        original.violator_pubkey = os.urandom(216)
        original.conflicts = [os.urandom(32), os.urandom(32), os.urandom(32)]
        original.signature = int.from_bytes(os.urandom(128), byteorder='big')

        raw = original.pack()
        restored = PenaltyTransaction()
        restored.parse(raw)

        self.assertEqual(original.get_hash(), restored.get_hash()) 

    def test_pack_parse_stakerelease_transaction(self):
        original = StakeReleaseTransaction()
        original.pubkey = os.urandom(216)
        original.signature = int.from_bytes(os.urandom(128), byteorder='big')

        raw = original.pack()
        restored = StakeReleaseTransaction()
        restored.parse(raw)

        self.assertEqual(original.get_hash(), restored.get_hash())        
        