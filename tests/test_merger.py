import unittest
from chain.block_factory import BlockFactory
from chain.dag import Dag
from chain.epoch import BLOCK_TIME
from chain.merger import Merger
from crypto.private import Private
from tests.test_chain_generator import TestChainGenerator
from visualization.dag_visualizer import DagVisualizer


class TestMerger(unittest.TestCase):

    def test_conflicts(self):
        dag = Dag(0)
        private = Private.generate()
        block1 = BlockFactory.create_block_with_timestamp([dag.genesis_block().get_hash()], BLOCK_TIME * 1)
        signed_block1 = BlockFactory.sign_block(block1, private)
        dag.add_signed_block(1, signed_block1)

        block2 = BlockFactory.create_block_with_timestamp([block1.get_hash()], BLOCK_TIME * 2)
        signed_block2 = BlockFactory.sign_block(block2, private)
        dag.add_signed_block(2, signed_block2)

        block3 = BlockFactory.create_block_with_timestamp([block2.get_hash()], BLOCK_TIME * 3)
        signed_block3 = BlockFactory.sign_block(block3, private)
        dag.add_signed_block(3, signed_block3)

        # alternative chain
        other_block2 = BlockFactory.create_block_with_timestamp([block1.get_hash()], BLOCK_TIME * 2 + 1)
        other_signed_block2 = BlockFactory.sign_block(other_block2, private)
        dag.add_signed_block(2, other_signed_block2)

        merger = Merger(dag)
        top, conflicts = merger.get_top_and_conflicts()

        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0], other_block2.get_hash())

        # TODO more complicated test to find conflicts in next epoch

    def test_merge(self):
        dag = Dag(0)
        prev_hash = dag.genesis_block().get_hash()
        TestChainGenerator.fill_with_dummies_and_skips(dag, prev_hash, range(1,4), [1,2])
        TestChainGenerator.fill_with_dummies_and_skips(dag, prev_hash, range(1,4), [3])
        
        merger = Merger(dag)
        res = merger.merge(dag.get_top_hashes())

        self.assertEqual(res[0], dag.blocks_by_number[0][0])
        self.assertEqual(res[1], dag.blocks_by_number[1][0])
        self.assertEqual(res[2], dag.blocks_by_number[2][0])
        self.assertEqual(res[3], dag.blocks_by_number[3][0])

    def test_complex_merge(self):
        dag = Dag(0)
        genesis_hash = dag.genesis_block().get_hash()
        TestChainGenerator.fill_with_dummies_and_skips(dag, genesis_hash, range(1,10), [2,5,7,8])
        first_block = dag.blocks_by_number[1][0].get_hash()
        TestChainGenerator.fill_with_dummies_and_skips(dag, first_block, range(2,10), [3,4,6,7,8,9])
        second_block = dag.blocks_by_number[2][0].get_hash()
        TestChainGenerator.fill_with_dummies_and_skips(dag, second_block, range(3,10), [3,4,5,6,9])
        
        merger = Merger(dag)
        res = merger.merge(dag.get_top_hashes())

        self.assertEqual(res[0], dag.blocks_by_number[1][0])
        self.assertEqual(res[1], dag.blocks_by_number[3][0])
        self.assertEqual(res[2], dag.blocks_by_number[4][0])
        self.assertEqual(res[3], dag.blocks_by_number[6][0])
        self.assertEqual(res[4], dag.blocks_by_number[9][0])
        self.assertEqual(res[5], dag.blocks_by_number[2][0])  # TODO find out why is this 2 here
        self.assertEqual(res[6], dag.blocks_by_number[7][0])
        self.assertEqual(res[7], dag.blocks_by_number[8][0])
        self.assertEqual(res[8], dag.blocks_by_number[5][0])

    def test_merge_with_conflict_simplest(self):
        dag = Dag(0)

        genesis_hash = dag.genesis_block().get_hash()

        block_hash1 = TestChainGenerator.insert_dummy(dag, [genesis_hash], 1)
        block_hash2 = TestChainGenerator.insert_dummy(dag, [genesis_hash], 1)

        # DagVisualizer.visualize(dag, True)  # uncomment for discover in visualization folder

        conflicts = [block_hash1]

        merger = Merger(dag)
        res = merger.merge(dag.get_top_hashes(), conflicts)

        self.assertEqual(res[0].get_hash(), genesis_hash)
        self.assertEqual(res[1].get_hash(), block_hash2)

    def test_merge_with_conflict_simple(self):
        dag = Dag(0)

        genesis_hash = dag.genesis_block().get_hash()

        block_hash1 = TestChainGenerator.insert_dummy(dag, [genesis_hash], 1)
        
        conflicting_block_hash1 = TestChainGenerator.insert_dummy(dag, [block_hash1], 2)
        conflicting_block_hash2 = TestChainGenerator.insert_dummy(dag, [block_hash1], 2)

        block_hash3 = TestChainGenerator.insert_dummy(dag, [conflicting_block_hash2], 3)

        # DagVisualizer.visualize(dag, True)  # uncomment for discover in visualization folder

        conflicts = [conflicting_block_hash1]
 
        merger = Merger(dag)
        res = merger.merge(dag.get_top_hashes(), conflicts)

        # self.assertEqual(res[0].get_hash(), genesis_hash) #no genesis hash since common ancestor is first block
        self.assertEqual(res[0].get_hash(), block_hash1)
        self.assertEqual(res[1].get_hash(), conflicting_block_hash2)
        self.assertEqual(res[2].get_hash(), block_hash3)






