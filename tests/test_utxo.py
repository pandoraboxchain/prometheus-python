import unittest
import os

from transaction.payment_transaction import PaymentTransaction
from transaction.utxo import Utxo, COINBASE_IDENTIFIER

class TestUtxo(unittest.TestCase):

    def test_add_outputs(self):
        output1 = os.urandom(32)
        output2 = os.urandom(32)
        payment = PaymentTransaction()
        payment.input = COINBASE_IDENTIFIER
        payment.number = 1
        payment.outputs = [output1, output2]
        payment.amounts = [123, 999]

        payment_hash = payment.get_hash()

        utxo = Utxo()
        utxo.add(payment)

        self.assertIn(payment_hash, utxo.utxo)
        self.assertEqual(len(utxo.utxo[payment_hash]), 2)
        self.assertEqual(utxo.utxo[payment_hash][0], 123)
        self.assertEqual(utxo.utxo[payment_hash][1], 999)

    def test_spend_input(self):
        prev_tx = os.urandom(32)
        utxo = Utxo()
        utxo.utxo[prev_tx] = { 0 : 300 } # predefine utxo

        payment = PaymentTransaction()
        payment.input = prev_tx
        payment.number = 0
        payment.outputs = [os.urandom(32), os.urandom(32)]
        payment.amounts = [149, 151]

        utxo.add(payment) # spend it

        payment_hash = payment.get_hash()

        self.assertNotIn(prev_tx, utxo.utxo)
        self.assertIn(payment_hash, utxo.utxo)
        self.assertEqual(utxo.utxo[payment_hash][0], 149)
        self.assertEqual(utxo.utxo[payment_hash][1], 151)
