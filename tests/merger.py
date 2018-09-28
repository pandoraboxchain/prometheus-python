import unittest
from chain.block_factory import BlockFactory
from chain.dag import Dag
from crypto.private import Private
from chain.epoch import BLOCK_TIME
from chain.merger import Merger
from tests.test_chain_generator import TestChainGenerator


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

    def test_common_ancestor(self):
        dag = TestChainGenerator.generate_two_chains(5)
        expected_intersection = dag.blocks_by_number[1][0].get_hash()
        
        merger = Merger(dag)
        tops = dag.get_top_blocks_hashes()
        found_intersection = merger.get_common_ancestor(tops[0], tops[1])

        self.assertEqual(expected_intersection, found_intersection)

    def test_merge(self):
        dag = Dag(0)
        prev_hash = dag.genesis_block().get_hash()
        TestChainGenerator.fill_with_dummies_and_skips(dag, prev_hash, range(1,4), [1,3])
        TestChainGenerator.fill_with_dummies_and_skips(dag, prev_hash, range(1,4), [2])
        
        from visualization.dag_visualizer import DagVisualizer
        DagVisualizer.visualize(dag, True)

        merger = Merger(dag)
        res = merger.merge()

        for block in res:
            if block:
                print(block.get_hash().hex())
            else:
                print("None")

        # self.assertEqual(res[0], zero)
        # self.assertEqual(res[1], first)
        # self.assertEqual(res[2], second)
        # self.assertEqual(res[3], third)

