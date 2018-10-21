import unittest
import os

from transaction.payment_transaction import PaymentTransaction
from chain.resolver import Resolver, Entry
from chain.merger import Merger
from chain.conflict_finder import ConflictFinder
from chain.conflict_watcher import ConflictWatcher
from chain.block_factory import BlockFactory
from chain.dag import Dag
from chain.transaction_factory import TransactionFactory
from chain.merging_iterator import MergingIter
from crypto.private import Private
from tests.test_chain_generator import TestChainGenerator


class TestConflictWatcher(unittest.TestCase):
    
    def test_simple(self):
        dag = Dag(0)
        conflict_watcher = ConflictWatcher(dag)

        actor1 = Private.publickey(Private.generate())
        actor2 = Private.publickey(Private.generate())
        actor3 = Private.publickey(Private.generate())

        block1_hash = TestChainGenerator.insert_dummy(dag, [dag.genesis_hash()], 1)
        conflict_watcher.on_new_block_by_validator(block1_hash, 1, actor1)

        block2_hash = TestChainGenerator.insert_dummy(dag, [block1_hash], 2)
        conflict_watcher.on_new_block_by_validator(block2_hash, 1, actor2)

        block2c_hash = TestChainGenerator.insert_dummy(dag, [block1_hash], 2)
        conflict_watcher.on_new_block_by_validator(block2c_hash, 1, actor2)

        block3_hash = TestChainGenerator.insert_dummy(dag, [block2_hash, block2c_hash], 3)
        conflict_watcher.on_new_block_by_validator(block3_hash, 1, actor3)

        conflicts = conflict_watcher.get_conflicts_by_block(block2_hash)
        self.assertEqual(len(conflicts), 2)
        self.assertIn(block2_hash, conflicts)
        self.assertIn(block2c_hash, conflicts)

        conflicts = conflict_watcher.get_conflicts_by_block(block1_hash)
        self.assertEqual(conflicts, None)


    #TODO test cross epoch