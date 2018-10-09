import unittest
from chain.block_factory import BlockFactory
from chain.dag import Dag
from chain.merging_iterator import MergingIter
from chain.params import BLOCK_TIME
from crypto.private import Private
from tests.test_chain_generator import TestChainGenerator
from visualization.dag_visualizer import DagVisualizer


class TestMergingIterator(unittest.TestCase):
    #TODO complex merge with recursive merge

    def test_simple_merge(self):
        dag = Dag(0)
        genesis_hash = dag.genesis_block().get_hash()
        TestChainGenerator.fill_with_dummies_and_skips(dag, genesis_hash, range(1,10), [2,5,7,8])
        first_block = dag.blocks_by_number[1][0].get_hash()
        TestChainGenerator.fill_with_dummies_and_skips(dag, first_block, range(2,10), [3,4,6,7,8,9])
        second_block = dag.blocks_by_number[2][0].get_hash()
        TestChainGenerator.fill_with_dummies_and_skips(dag, second_block, range(3,10), [3,4,5,6,9])

        hanging_tips = dag.get_top_hashes()

        merging_block = BlockFactory.create_block_with_timestamp(hanging_tips, BLOCK_TIME * 10)
        merging_signed_block = BlockFactory.sign_block(merging_block, Private.generate())
        dag.add_signed_block(10, merging_signed_block)
        # DagVisualizer.visualize(dag, True)
        
        iterator = MergingIter(dag, merging_block.get_hash())

        self.assertEqual(iterator.next().get_hash(), merging_block.get_hash())
        self.assertEqual(iterator.next().get_hash(), dag.blocks_by_number[5][0].get_hash())
        self.assertEqual(iterator.next().get_hash(), dag.blocks_by_number[8][0].get_hash())
        self.assertEqual(iterator.next().get_hash(), dag.blocks_by_number[7][0].get_hash())
        self.assertEqual(iterator.next().get_hash(), dag.blocks_by_number[2][0].get_hash()) #TODO find out why is this 2 here
        self.assertEqual(iterator.next().get_hash(), dag.blocks_by_number[9][0].get_hash())
        self.assertEqual(iterator.next().get_hash(), dag.blocks_by_number[6][0].get_hash())
        self.assertEqual(iterator.next().get_hash(), dag.blocks_by_number[4][0].get_hash())
        self.assertEqual(iterator.next().get_hash(), dag.blocks_by_number[3][0].get_hash())
        self.assertEqual(iterator.next().get_hash(), dag.blocks_by_number[1][0].get_hash())
        self.assertEqual(iterator.next().get_hash(), dag.blocks_by_number[0][0].get_hash())

    def test_merge_in_merge(self):
        dag = Dag(0)
        genesis_hash = dag.genesis_block().get_hash()
        TestChainGenerator.fill_with_dummies_and_skips(dag, genesis_hash, range(1,5), [1,3])
        second_block = dag.blocks_by_number[2][0].get_hash()
        TestChainGenerator.fill_with_dummies_and_skips(dag, second_block, range(3,4), [])
        tops = dag.get_top_hashes()
        merging_block = BlockFactory.create_block_with_timestamp(tops, BLOCK_TIME * 5)
        merging_signed_block = BlockFactory.sign_block(merging_block, Private.generate())
        dag.add_signed_block(5, merging_signed_block)

        TestChainGenerator.fill_with_dummies_and_skips(dag, genesis_hash, range(1,7), [2,3,4,5])

        tops = dag.get_top_hashes()
        merging_block = BlockFactory.create_block_with_timestamp(tops, BLOCK_TIME * 7)
        merging_signed_block = BlockFactory.sign_block(merging_block, Private.generate())
        dag.add_signed_block(7, merging_signed_block)

        DagVisualizer.visualize(dag, True)        

        # block = BlockFactory.create_block_with_timestamp([merging_block.get_hash()], BLOCK_TIME * 6)
        # signed_block = BlockFactory.sign_block(block, Private.generate())
        # dag.add_signed_block(6, signed_block)

        iterator = MergingIter(dag, merging_block.get_hash())

        for block in iterator:
            print(dag.get_block_number(block.get_hash()))
            
        # self.assertEqual(iterator.next().get_hash(), dag.blocks_by_number[7][0].get_hash())
        # self.assertEqual(iterator.next().get_hash(), dag.blocks_by_number[6][0].get_hash())
        # self.assertEqual(iterator.next().get_hash(), dag.blocks_by_number[5][0].get_hash())
        # self.assertEqual(iterator.next().get_hash(), dag.blocks_by_number[4][0].get_hash())
        # self.assertEqual(iterator.next().get_hash(), dag.blocks_by_number[3][0].get_hash())
        # self.assertEqual(iterator.next().get_hash(), dag.blocks_by_number[2][0].get_hash())
        # self.assertEqual(iterator.next().get_hash(), dag.blocks_by_number[1][0].get_hash())
        # self.assertEqual(iterator.next().get_hash(), dag.blocks_by_number[0][0].get_hash())