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

        block_hash = TestChainGenerator.insert_dummy_with_payments(dag, [dag.genesis_hash()], [], 1)
        block_reward = dag.blocks_by_hash[block_hash].block.payment_txs[0]

        payment = TransactionFactory.create_payment(block_reward.get_hash(), 0, [os.urandom(32)], [12])
        block2_hash = TestChainGenerator.insert_dummy_with_payments(dag, [block_hash], [payment], 2)
        block2_reward = dag.blocks_by_hash[block2_hash].block.payment_txs[0]

        iterator = MergingIter(dag, block2_hash)
        payments = [block.block.payment_txs for block in iterator]
        payments = list(reversed(payments))

        spent, unspent = Resolver.resolve(payments)

        self.assertEqual(len(spent), 0)

        self.assertIn(Entry(block2_reward.get_hash(), 0), unspent)
        self.assertIn(Entry(payment.get_hash(), 0), unspent)




