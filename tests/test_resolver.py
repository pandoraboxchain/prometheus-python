import unittest
import os

from transaction.payment_transaction import PaymentTransaction
from chain.transaction_factory import TransactionFactory
from chain.resolver import Resolver, Entry

class TestResolver(unittest.TestCase):

    def test_ignore_coinbase(self):
        block_reward = TransactionFactory.create_block_reward(os.urandom(32), 0)
        
        payment = PaymentTransaction()
        payment.input = block_reward.get_hash()
        payment.number = 0
        payment.outputs = [os.urandom(32), os.urandom(32)]
        payment.amounts = [129, 23423]

        spent, unspent = Resolver.resolve([[block_reward, payment]])
        
        #nothing spent since block reward just creates outputs
        self.assertEqual(len(spent), 0)

        #block reward was split in two ouputs by payment transaction
        self.assertEqual(len(unspent), 2)
        self.assertIn(Entry(payment.get_hash(), 0), unspent)
        self.assertIn(Entry(payment.get_hash(), 1), unspent)

    def test_simple(self):
        input1 = os.urandom(32)
        payment1 = PaymentTransaction()
        payment1.input = input1
        payment1.number = 0
        payment1.outputs = [os.urandom(32), os.urandom(32)]
        payment1.amounts = [123, 999]

        payment1_hash = payment1.get_hash()

        output3 = os.urandom(32)
        output4 = os.urandom(32)
        payment2 = PaymentTransaction()
        payment2.input = payment1_hash
        payment2.number = 0
        payment2.outputs = [output3, output4]
        payment2.amounts = [555, 234]

        payment2_hash = payment2.get_hash()

        spent, unspent = Resolver.resolve([[payment1], [payment2]])

        #zero input of random transaction should be marked as spent
        self.assertEqual(len(spent), 1)
        self.assertEqual(spent[0].tx, input1)
        self.assertEqual(spent[0].number, 0)

        #zero output of payment1 tx is spent by payment2, so only 3 unspent outputs left here
        self.assertEqual(len(unspent), 3)
        self.assertIn(Entry(payment1_hash, 1), unspent)
        self.assertIn(Entry(payment2_hash, 0), unspent)
        self.assertIn(Entry(payment2_hash, 1), unspent)

    def test_conflict(self):
        input1 = os.urandom(32)
        payment1 = PaymentTransaction()
        payment1.input = input1
        payment1.number = 0
        payment1.outputs = [os.urandom(32), os.urandom(32)]
        payment1.amounts = [123, 999]

        payment1_hash = payment1.get_hash()

        # trying to spend the same input
        payment2 = PaymentTransaction()
        payment2.input = input1
        payment2.number = 0
        payment2.outputs = [os.urandom(32), os.urandom(32)]
        payment2.amounts = [1, 1]

        spent, unspent = Resolver.resolve([[payment1, payment2]]) #TODO is it okay that conflicting transactions are in the same block

        #zero input of random transaction should be marked as spent
        self.assertEqual(len(spent), 1)
        self.assertEqual(spent[0].tx, input1)
        self.assertEqual(spent[0].number, 0)

        #transaction spending the same output is rejected
        self.assertEqual(len(unspent), 2)
        self.assertIn(Entry(payment1_hash, 0), unspent)
        self.assertIn(Entry(payment1_hash, 1), unspent)



