import unittest
import os
from chain.block import Block
from chain.signed_block import SignedBlock
from chain.block_factory import BlockFactory
from chain.dag import Dag
from crypto.private import Private
from chain.epoch import BLOCK_TIME
from chain.dag import ChainIter

class TestDag(unittest.TestCase):

    def test_top_blocks(self):
        dag = Dag(0)
        private = Private.generate()
        block1 = BlockFactory.create_block_with_timestamp([dag.genesis_block().get_hash()], BLOCK_TIME)
        signed_block1 = BlockFactory.sign_block(block1, private)
        dag.add_signed_block(1, signed_block1)

        block2 = BlockFactory.create_block_with_timestamp([block1.get_hash()], BLOCK_TIME * 2)
        signed_block2 = BlockFactory.sign_block(block2, private)
        dag.add_signed_block(2, signed_block2)

        block3 = BlockFactory.create_block_with_timestamp([block1.get_hash()], BLOCK_TIME * 3)
        signed_block3 = BlockFactory.sign_block(block3, private)
        dag.add_signed_block(3, signed_block3)

        top_hashes = list(dag.get_top_blocks().keys());

        self.assertEqual(top_hashes[0], block2.get_hash())
        self.assertEqual(top_hashes[1], block3.get_hash())

    def test_chain_length(self):
        dag = Dag(0)
        private = Private.generate()
        block1 = BlockFactory.create_block_with_timestamp([dag.genesis_block().get_hash()], BLOCK_TIME)
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
        

        self.assertEqual(dag.calculate_chain_length(other_block2.get_hash()), 3)
        self.assertEqual(dag.calculate_chain_length(block3.get_hash()), 4)

    def test_ancestry(self):
        dag = Dag(0)
        private = Private.generate()
        block1 = BlockFactory.create_block_with_timestamp([dag.genesis_block().get_hash()], BLOCK_TIME)
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

        # alternative chain
        other_block3 = BlockFactory.create_block_with_timestamp([other_block2.get_hash()], BLOCK_TIME * 3 + 1)
        other_signed_block3 = BlockFactory.sign_block(other_block3, private)
        dag.add_signed_block(3, other_signed_block3)
        
        self.assertEqual(dag.is_ancestor(other_block3.get_hash(), other_block2.get_hash()), True)
        self.assertEqual(dag.is_ancestor(other_block3.get_hash(), block2.get_hash()), False)

    def test_iterator(self):
        dag = Dag(0)
        private = Private.generate()
        block1 = BlockFactory.create_block_with_timestamp([dag.genesis_block().get_hash()], BLOCK_TIME)
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

        #intentionally skipped block

        # alternative chain
        other_block4 = BlockFactory.create_block_with_timestamp([other_block2.get_hash()], BLOCK_TIME * 3 + 1)
        other_signed_block4 = BlockFactory.sign_block(other_block4, private)
        dag.add_signed_block(4, other_signed_block4)

        chain_iter = ChainIter(dag, block3.get_hash())
        self.assertEqual(chain_iter.next().block.get_hash(), block3.get_hash())
        self.assertEqual(chain_iter.next().block.get_hash(), block2.get_hash())
        self.assertEqual(chain_iter.next().block.get_hash(), block1.get_hash())

        chain_iter = ChainIter(dag, other_block4.get_hash())
        self.assertEqual(chain_iter.next().block.get_hash(), other_block4.get_hash())
        self.assertEqual(chain_iter.next(), None)   #detect intentionally skipped block
        self.assertEqual(chain_iter.next().block.get_hash(), other_block2.get_hash())
        self.assertEqual(chain_iter.next().block.get_hash(), block1.get_hash())
