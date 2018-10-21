import unittest
import os

from transaction.payment_transaction import PaymentTransaction
from chain.resolver import Resolver, Entry
from chain.merger import Merger
from chain.conflict_finder import ConflictFinder
from chain.block_factory import BlockFactory
from chain.dag import Dag
from chain.transaction_factory import TransactionFactory
from chain.merging_iterator import MergingIter
from tests.test_chain_generator import TestChainGenerator

class TestMergeAndResolve(unittest.TestCase):
    def test_simple(self):
        dag = Dag(0)

        block_hash, block_reward = TestChainGenerator.insert_dummy_with_payments(dag, [dag.genesis_hash()], [], 1)

        payment = TransactionFactory.create_payment(block_reward, 0, [os.urandom(32)], [12])
        block2_hash, block2_reward = TestChainGenerator.insert_dummy_with_payments(dag, [block_hash], [payment], 2)

        iterator = MergingIter(dag, block2_hash)
        payments = [block.block.payment_txs for block in iterator]
        payments = list(reversed(payments))

        spent, unspent = Resolver.resolve(payments)

        self.assertEqual(len(spent), 0)

        self.assertIn(Entry(block2_reward, 0), unspent)
        self.assertIn(Entry(payment.get_hash(), 0), unspent)

    def test_merged_chain_without_transaction_conflicts(self):
        dag = Dag(0)

        block_hash, block_reward = TestChainGenerator.insert_dummy_with_payments(dag, [dag.genesis_hash()], [], 1)

        payment1 = TransactionFactory.create_payment(block_reward, 0, [os.urandom(32)], [15])
        block2_hash, block2_reward = TestChainGenerator.insert_dummy_with_payments(dag, [block_hash], [payment1], 2)

        payment2 = TransactionFactory.create_payment(block2_reward, 0, [os.urandom(32)], [15])
        block3_hash, block3_reward = TestChainGenerator.insert_dummy_with_payments(dag, [block_hash], [payment2], 3)

        block4_hash, block4_reward = TestChainGenerator.insert_dummy_with_payments(dag, [block2_hash, block3_hash], [], 4)

        iterator = MergingIter(dag, block4_hash)
        payments = [block.block.payment_txs for block in iterator if block != None]
        payments = list(reversed(payments))

        spent, unspent = Resolver.resolve(payments)

        self.assertEqual(len(spent), 0)

        self.assertEqual(len(unspent), 4)

        self.assertIn(Entry(block3_reward, 0), unspent)
        self.assertIn(Entry(block4_reward, 0), unspent)
        self.assertIn(Entry(payment1.get_hash(), 0), unspent)
        self.assertIn(Entry(payment2.get_hash(), 0), unspent)

    def test_merged_chain_with_transaction_conflicts(self):
        dag = Dag(0)

        block_hash, block_reward = TestChainGenerator.insert_dummy_with_payments(dag, [dag.genesis_hash()], [], 1)

        #second block spends first block reward
        payment1 = TransactionFactory.create_payment(block_reward, 0, [os.urandom(32)], [15])
        block2_hash, block2_reward = TestChainGenerator.insert_dummy_with_payments(dag, [block_hash], [payment1], 2)

        #third block also spends first block reward
        payment2 = TransactionFactory.create_payment(block_reward, 0, [os.urandom(32)], [15])
        block3_hash, block3_reward = TestChainGenerator.insert_dummy_with_payments(dag, [block_hash], [payment2], 3)

        #making block2_hash go first, so its transactions will have a priority
        block4_hash, block4_reward = TestChainGenerator.insert_dummy_with_payments(dag, [block2_hash, block3_hash], [], 4)

        iterator = MergingIter(dag, block4_hash)
        payments = [block.block.payment_txs for block in iterator if block != None]
        payments = list(reversed(payments))

        spent, unspent = Resolver.resolve(payments)

        self.assertEqual(len(spent), 0)

        self.assertEqual(len(unspent), 4)

        self.assertIn(Entry(block2_reward, 0), unspent)
        self.assertIn(Entry(block3_reward, 0), unspent)
        self.assertIn(Entry(block4_reward, 0), unspent)
        self.assertIn(Entry(payment1.get_hash(), 0), unspent)
        self.assertNotIn(Entry(payment2.get_hash(), 0), unspent) #payment 2 is consedered conflicting as it goes later in merged chain



