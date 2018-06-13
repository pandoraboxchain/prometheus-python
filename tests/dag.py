import unittest
import os
from chain.block import Block
from chain.signed_block import SignedBlock
from chain.block_factory import BlockFactory
from chain.dag import Dag
from crypto.private import Private
from chain.epoch import BLOCK_TIME

class TestDag(unittest.TestCase):

    def test_top_blocks(self):
        dag = Dag(0)
        private = Private.generate()
        block1 = BlockFactory.create_block_with_timestamp([dag.genesis_block().get_hash().digest()], BLOCK_TIME)
        signed_block1 = BlockFactory.sign_block(block1, private)
        dag.add_signed_block(1, signed_block1)

        block2 = BlockFactory.create_block_with_timestamp([block1.get_hash().digest()], BLOCK_TIME * 2)
        signed_block2 = BlockFactory.sign_block(block2, private)
        dag.add_signed_block(2, signed_block2)

        block3 = BlockFactory.create_block_with_timestamp([block1.get_hash().digest()], BLOCK_TIME * 3)
        signed_block3 = BlockFactory.sign_block(block3, private)
        dag.add_signed_block(3, signed_block3)

        top_hashes = list(dag.get_top_blocks().keys());

        self.assertEqual(top_hashes[0], block2.get_hash().digest())
        self.assertEqual(top_hashes[1], block3.get_hash().digest())

    def test_chain_length(self):
        dag = Dag(0)
        private = Private.generate()
        block1 = BlockFactory.create_block_dummy([dag.genesis_block().get_hash().digest()])
        signed_block1 = BlockFactory.sign_block(block1, private)
        dag.add_signed_block(1, signed_block1)

        block2 = BlockFactory.create_block_dummy([block1.get_hash().digest()])
        signed_block2 = BlockFactory.sign_block(block2, private)
        dag.add_signed_block(2, signed_block2)

        block3 = BlockFactory.create_block_dummy([block2.get_hash().digest()])
        signed_block3 = BlockFactory.sign_block(block3, private)
        dag.add_signed_block(3, signed_block3)

        # alternative chain
        other_block2 = BlockFactory.create_block_dummy([block1.get_hash().digest()])
        other_signed_block2 = BlockFactory.sign_block(other_block2, private)
        dag.add_signed_block(2, other_signed_block2)

        self.assertEqual(dag.calculate_chain_length(other_block2.get_hash().digest()), 3)
        self.assertEqual(dag.calculate_chain_length(block3.get_hash().digest()), 4)




        


        
