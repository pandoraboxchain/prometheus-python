import os

from chain.block import Block
from chain.signed_block import SignedBlock
from chain.block_factory import BlockFactory
from chain.dag import Dag
from crypto.private import Private
from chain.epoch import BLOCK_TIME

class TestChainGenerator:
    
    @staticmethod
    def generate_two_chains(length):
        dag = Dag(0)
        private = Private.generate()
        prev_hash = dag.genesis_block().get_hash()
        for i in range(1, length + 1):
            block = BlockFactory.create_block_with_timestamp([prev_hash], BLOCK_TIME * i)
            signed_block = BlockFactory.sign_block(block, private)
            dag.add_signed_block(i, signed_block)
            prev_hash = block.get_hash()

        prev_hash = dag.blocks_by_number[1][0].get_hash()
        for i in range(1, length + 1):  #intentionally one block less
            if i == 4: continue #intentionally skipped block
            block = BlockFactory.create_block_with_timestamp([prev_hash], BLOCK_TIME * i + 1)
            signed_block = BlockFactory.sign_block(block, private)
            dag.add_signed_block(i, signed_block)
            prev_hash = block.get_hash()

        return dag

    @staticmethod
    def fill_with_dummies(dag, prev_hash, start, end):
        dummy_private = Private.generate()
        for i in range(start, end):
            block = BlockFactory.create_block_with_timestamp([prev_hash], BLOCK_TIME * i)
            signed_block = BlockFactory.sign_block(block, dummy_private)
            dag.add_signed_block(i, signed_block)
            prev_hash = block.get_hash()
        
        return prev_hash
