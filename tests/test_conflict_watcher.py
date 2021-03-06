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
from tools.chain_generator import ChainGenerator


class TestConflictWatcher(unittest.TestCase):
    
    def test_same_timeslot_watch(self):
        dag = Dag(0)
        conflict_watcher = ConflictWatcher(dag)

        actor1 = Private.publickey(Private.generate())
        actor2 = Private.publickey(Private.generate())
        actor3 = Private.publickey(Private.generate())

        block1_hash = ChainGenerator.insert_dummy(dag, [dag.genesis_hash()], 1)
        conflict_watcher.on_new_block_by_validator(block1_hash, 1, actor1)

        block2_hash = ChainGenerator.insert_dummy(dag, [block1_hash], 2)
        conflict_watcher.on_new_block_by_validator(block2_hash, 1, actor2)

        block2c_hash = ChainGenerator.insert_dummy(dag, [block1_hash], 2)
        conflict_watcher.on_new_block_by_validator(block2c_hash, 1, actor2)

        block3_hash = ChainGenerator.insert_dummy(dag, [block2_hash, block2c_hash], 3)
        conflict_watcher.on_new_block_by_validator(block3_hash, 1, actor3)

        conflicts = conflict_watcher.get_conflicts_by_block(block2_hash)
        self.assertEqual(len(conflicts), 2)
        self.assertIn(block2_hash, conflicts)
        self.assertIn(block2c_hash, conflicts)

        conflicts = conflict_watcher.get_conflicts_by_block(block1_hash)
        self.assertEqual(conflicts, None)


    def test_different_timeslot_watch(self):
        dag = Dag(0)
        conflict_watcher = ConflictWatcher(dag)

        actor1 = Private.publickey(Private.generate())
        actor2 = Private.publickey(Private.generate())
        actor3 = Private.publickey(Private.generate())

        block1_hash = ChainGenerator.insert_dummy(dag, [dag.genesis_hash()], 1)
        conflict_watcher.on_new_block_by_validator(block1_hash, 1, actor1)

        block2_hash = ChainGenerator.insert_dummy(dag, [block1_hash], 2)
        conflict_watcher.on_new_block_by_validator(block2_hash, 1, actor2)

        # second block is signed by third validator
        # its not possible by usual means, but quite possible when we have two different epoch seeds
        block2c_hash = ChainGenerator.insert_dummy(dag, [block1_hash], 2)
        conflict_watcher.on_new_block_by_validator(block2c_hash, 1, actor3)

        block3_hash = ChainGenerator.insert_dummy(dag, [block2_hash, block2c_hash], 3)
        conflict_watcher.on_new_block_by_validator(block3_hash, 1, actor3)

        conflicts = conflict_watcher.get_conflicts_by_block(block3_hash)
        self.assertEqual(len(conflicts), 2)
        self.assertIn(block2c_hash, conflicts)
        self.assertIn(block3_hash, conflicts)

    def test_different_epoch_watch(self):
        dag = Dag(0)
        conflict_watcher = ConflictWatcher(dag)

        actor1 = Private.publickey(Private.generate())
        actor2 = Private.publickey(Private.generate())
        actor3 = Private.publickey(Private.generate())

        block1_hash = ChainGenerator.insert_dummy(dag, [dag.genesis_hash()], 1)
        conflict_watcher.on_new_block_by_validator(block1_hash, 1, actor1)

        block2_hash = ChainGenerator.insert_dummy(dag, [block1_hash], 2)
        conflict_watcher.on_new_block_by_validator(block2_hash, 1, actor2)

        block2c_hash = ChainGenerator.insert_dummy(dag, [block1_hash], 2)
        conflict_watcher.on_new_block_by_validator(block2c_hash, 1, actor2)

        block3_hash = ChainGenerator.insert_dummy(dag, [block2_hash, block2c_hash], 3)
        conflict_watcher.on_new_block_by_validator(block3_hash, 1, actor3)

        #switch to next epoch
        block4_hash = ChainGenerator.insert_dummy(dag, [block3_hash], 4)
        conflict_watcher.on_new_block_by_validator(block4_hash, 2, actor2) 
        
        block4c_hash = ChainGenerator.insert_dummy(dag, [block3_hash], 4)
        conflict_watcher.on_new_block_by_validator(block4c_hash, 2, actor2)

        #first epoch conflicts
        conflicts = conflict_watcher.get_conflicts_by_block(block2_hash)
        self.assertEqual(len(conflicts), 2)
        self.assertIn(block2_hash, conflicts)
        self.assertIn(block2c_hash, conflicts)

        #second epoch conflicts of the same public key
        conflicts = conflict_watcher.get_conflicts_by_block(block4_hash)
        self.assertEqual(len(conflicts), 2)
        self.assertIn(block4_hash, conflicts)
        self.assertIn(block4c_hash, conflicts)

        conflicts = conflict_watcher.get_conflicts_by_block(block1_hash)
        self.assertEqual(conflicts, None)

    def test_find_conflicts(self):
        dag = Dag(0)
        watcher = ConflictWatcher(dag)

        actor1 = Private.publickey(Private.generate())
        actor2 = Private.publickey(Private.generate())

        block1_hash = ChainGenerator.insert_dummy(dag, [dag.genesis_hash()], 1)
        watcher.on_new_block_by_validator(block1_hash, 1, actor1)

        block2_hash = ChainGenerator.insert_dummy(dag, [block1_hash], 2)
        watcher.on_new_block_by_validator(block2_hash, 1, actor2)

        block2c_hash = ChainGenerator.insert_dummy(dag, [block1_hash], 2)
        watcher.on_new_block_by_validator(block2c_hash, 1, actor2)

        # block3_hash = ChainGenerator.insert_dummy(dag, [block2_hash, block2c_hash], 3)
        # watcher.on_new_block_by_validator(block3_hash, 1, actor3)

        tops = dag.get_top_hashes()

        explicits, candidate_groups = watcher.find_conflicts_in_between(tops)
        self.assertEqual(len(explicits), 0)
        self.assertEqual(len(candidate_groups), 1)
        self.assertEqual(len(candidate_groups[0]), 2)
        self.assertIn(block2_hash, candidate_groups[0])
        self.assertIn(block2c_hash, candidate_groups[0])

    def test_explicit_conflict(self):
        dag = Dag(0)
        watcher = ConflictWatcher(dag)

        actor1 = Private.publickey(Private.generate())
        actor2 = Private.publickey(Private.generate())

        block1_hash = ChainGenerator.insert_dummy(dag, [dag.genesis_hash()], 1)
        watcher.on_new_block_by_validator(block1_hash, 1, actor2)
        
        block2_hash = ChainGenerator.insert_dummy(dag, [block1_hash], 2)
        watcher.on_new_block_by_validator(block2_hash, 1, actor1)

        block3_hash = ChainGenerator.insert_dummy(dag, [block2_hash], 3)
        watcher.on_new_block_by_validator(block3_hash, 1, actor2)

        block3c_hash = ChainGenerator.insert_dummy(dag, [block2_hash], 3)
        watcher.on_new_block_by_validator(block3c_hash, 1, actor2)

        tops = dag.get_top_hashes()

        #here block was signed by node even before merge appeared
        #this is explicit merge and both following blocks are conflicting
        explicits, candidates = watcher.find_conflicts_in_between(tops)
        self.assertEqual(len(explicits), 2)
        self.assertEqual(len(candidates), 0)
        self.assertIn(block3_hash, explicits)
        self.assertIn(block3c_hash, explicits)

    def test_explicit_conflict_right_on_common_ancestor(self):
        dag = Dag(0)
        watcher = ConflictWatcher(dag)

        actor2 = Private.publickey(Private.generate())

        #consider common ancestor already resolved
        block1_hash = ChainGenerator.insert_dummy(dag, [dag.genesis_hash()], 1)
        watcher.on_new_block_by_validator(block1_hash, 1, actor2)
        
        block2_hash = ChainGenerator.insert_dummy(dag, [block1_hash], 2)
        watcher.on_new_block_by_validator(block2_hash, 1, actor2)

        block2c_hash = ChainGenerator.insert_dummy(dag, [block1_hash], 2)
        watcher.on_new_block_by_validator(block2c_hash, 1, actor2)

        tops = dag.get_top_hashes()

        explicits, candidates = watcher.find_conflicts_in_between(tops)
        self.assertEqual(len(explicits), 2)
        self.assertEqual(len(candidates), 0)
        self.assertIn(block2_hash, explicits)
        self.assertIn(block2c_hash, explicits)

    def test_both_types_of_conflicts(self):
        dag = Dag(0)
        watcher = ConflictWatcher(dag)

        actor1 = Private.publickey(Private.generate())
        actor2 = Private.publickey(Private.generate())
        actor3 = Private.publickey(Private.generate())

        block1_hash = ChainGenerator.insert_dummy(dag, [dag.genesis_hash()], 1)
        watcher.on_new_block_by_validator(block1_hash, 1, actor1)
        
        block2_hash = ChainGenerator.insert_dummy(dag, [block1_hash], 2)
        watcher.on_new_block_by_validator(block2_hash, 1, actor2)

        block2c_hash = ChainGenerator.insert_dummy(dag, [block1_hash], 2)
        watcher.on_new_block_by_validator(block2c_hash, 1, actor2)

        block3_hash = ChainGenerator.insert_dummy(dag, [block2_hash], 3)
        watcher.on_new_block_by_validator(block3_hash, 1, actor3)

        #this is possible if we have two epoch seeds
        block4_hash = ChainGenerator.insert_dummy(dag, [block2c_hash], 4)
        watcher.on_new_block_by_validator(block4_hash, 1, actor1)

        tops = dag.get_top_hashes()

        explicits, candidate_groups = watcher.find_conflicts_in_between(tops)
        self.assertEqual(len(explicits), 1)
        self.assertIn(block4_hash, explicits)

        self.assertEqual(len(candidate_groups), 1)
        self.assertEqual(len(candidate_groups[0]), 2)
        self.assertIn(block2_hash, candidate_groups[0])
        self.assertIn(block2c_hash, candidate_groups[0])

    def test_filtering_longest_chain(self):
        dag = Dag(0)
        watcher = ConflictWatcher(dag)
        
        actor1 = Private.publickey(Private.generate())
        actor2 = Private.publickey(Private.generate())

        block1_hash = ChainGenerator.insert_dummy(dag, [dag.genesis_hash()], 1)
        watcher.on_new_block_by_validator(block1_hash, 1, actor1)

        block2_hash = ChainGenerator.insert_dummy(dag, [block1_hash], 2)
        watcher.on_new_block_by_validator(block2_hash, 1, actor2)

        block2c_hash = ChainGenerator.insert_dummy(dag, [block1_hash], 2)
        watcher.on_new_block_by_validator(block2c_hash, 1, actor2)

        tops = dag.get_top_hashes()

        explicits, candidate_groups = watcher.find_conflicts_in_between(tops)
        self.assertEqual(len(explicits), 0)
        self.assertEqual(len(candidate_groups), 1)
        self.assertEqual(len(candidate_groups[0]), 2)
        self.assertIn(block2_hash, candidate_groups[0])
        self.assertIn(block2c_hash, candidate_groups[0])

        non_longest_chain_conflicts = watcher.filter_out_longest_chain_conflicts(candidate_groups, block2_hash)

        self.assertIn(block2c_hash, non_longest_chain_conflicts)
        self.assertNotIn(block2_hash, non_longest_chain_conflicts)

        non_longest_chain_conflicts = watcher.filter_out_longest_chain_conflicts(candidate_groups, block2c_hash)

        self.assertIn(block2_hash, non_longest_chain_conflicts)
        self.assertNotIn(block2c_hash, non_longest_chain_conflicts)

    #TODO test cross epoch
