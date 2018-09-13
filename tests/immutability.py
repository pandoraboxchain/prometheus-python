import unittest
import os
from chain.block import Block
from chain.signed_block import SignedBlock
from chain.block_factory import BlockFactory
from chain.dag import Dag
from crypto.private import Private
from chain.epoch import BLOCK_TIME
from chain.merger import Merger
from chain.immutability import Immutability
from chain.skipped_block import SkippedBlock

class TestImmutability(unittest.TestCase):
    def test_zeta_calculation(self):
        dag = Dag(0)
        private = Private.generate()
        prev_hash = dag.genesis_block().get_hash()
        for i in range(1, 3):
            block = BlockFactory.create_block_with_timestamp([prev_hash], BLOCK_TIME * i)
            signed_block = BlockFactory.sign_block(block, private)
            dag.add_signed_block(i, signed_block)
            prev_hash = block.get_hash()

        #skip 3 blocks

        for i in range(6, 7):
            block = BlockFactory.create_block_with_timestamp([prev_hash], BLOCK_TIME * i)
            signed_block = BlockFactory.sign_block(block, private)
            dag.add_signed_block(i, signed_block)
            prev_hash = block.get_hash()
        
        for i in range(10, 12):
            block = BlockFactory.create_block_with_timestamp([prev_hash], BLOCK_TIME * i)
            signed_block = BlockFactory.sign_block(block, private)
            dag.add_signed_block(i, signed_block)
            prev_hash = block.get_hash()

        prev_hash = dag.blocks_by_number[1][0].get_hash()
        for i in range(2, 12):
            if i == 3: continue
            block = BlockFactory.create_block_with_timestamp([prev_hash], BLOCK_TIME * i + 1)
            signed_block = BlockFactory.sign_block(block, private)
            dag.add_signed_block(i, signed_block)
            prev_hash = block.get_hash()

        from visualization.dag_visualizer import DagVisualizer
        DagVisualizer.visualize(dag, False)

        immutability = Immutability(dag)
        # zeta = immutability.calculate_zeta(dag.blocks_by_number[2][0].get_hash())
        # self.assertEqual(zeta, -2)

        zeta = immutability.calculate_zeta(dag.blocks_by_number[6][1].get_hash())
        self.assertEqual(zeta, 1)


    def test_confirmations_calculation(self):
        dag = Dag(0)
        private = Private.generate()
        prev_hash = dag.genesis_block().get_hash()
        for i in range(1, 9):
            if i == 5 or i == 7: continue
            block = BlockFactory.create_block_with_timestamp([prev_hash], BLOCK_TIME * i)
            signed_block = BlockFactory.sign_block(block, private)
            dag.add_signed_block(i, signed_block)
            prev_hash = block.get_hash()

        prev_hash = dag.blocks_by_number[1][0].get_hash()
        for i in range(2, 5):
            if i == 3: continue
            block = BlockFactory.create_block_with_timestamp([prev_hash], BLOCK_TIME * i + 1)
            signed_block = BlockFactory.sign_block(block, private)
            dag.add_signed_block(i, signed_block)
            prev_hash = block.get_hash()

        immutability = Immutability(dag)

        #first branch check
        confirmations = immutability.calculate_confirmations(dag.blocks_by_number[8][0].get_hash())
        self.assertEqual(confirmations, 0)

        skipped_block = SkippedBlock(dag.blocks_by_number[8][0].get_hash(), backstep_count=1)
        confirmations = immutability.calculate_skipped_block_confirmations(skipped_block)
        self.assertEqual(confirmations, 1)

        confirmations = immutability.calculate_confirmations(dag.blocks_by_number[6][0].get_hash())
        self.assertEqual(confirmations, 1)

        skipped_block = SkippedBlock(dag.blocks_by_number[6][0].get_hash(), backstep_count=1)
        confirmations = immutability.calculate_skipped_block_confirmations(skipped_block)
        self.assertEqual(confirmations, 2)

        confirmations = immutability.calculate_confirmations(dag.blocks_by_number[4][0].get_hash())
        self.assertEqual(confirmations, 2)

        #second branch check
        confirmations = immutability.calculate_confirmations(dag.blocks_by_number[4][1].get_hash())
        self.assertEqual(confirmations, 0)
        
        skipped_block = SkippedBlock(dag.blocks_by_number[4][1].get_hash(), backstep_count=1)
        confirmations = immutability.calculate_skipped_block_confirmations(skipped_block)
        self.assertEqual(confirmations, 1)

        confirmations = immutability.calculate_confirmations(dag.blocks_by_number[2][1].get_hash())
        self.assertEqual(confirmations, 1)

        #common ancestor
        #four existing blocks in the following five slots
        confirmations = immutability.calculate_confirmations(dag.blocks_by_number[1][0].get_hash())
        self.assertEqual(confirmations, 4)

        # self.assertEqual(conflicts[0], other_block2.get_hash())



        


        
