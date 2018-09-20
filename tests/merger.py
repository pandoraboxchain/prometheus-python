import unittest
import os
from chain.block import Block
from chain.signed_block import SignedBlock
from chain.block_factory import BlockFactory
from chain.dag import Dag
from crypto.private import Private
from chain.epoch import BLOCK_TIME
from chain.merger import Merger

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



        


        
