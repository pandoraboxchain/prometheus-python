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
        for i in range(2, length + 1):  # intentionally one block less
            if i == 4: continue  # intentionally skipped block
            block = BlockFactory.create_block_with_timestamp([prev_hash], BLOCK_TIME * i + 1)
            signed_block = BlockFactory.sign_block(block, private)
            dag.add_signed_block(i, signed_block)
            prev_hash = block.get_hash()

        return dag

    # TODO creater similar but simpler method not using prev_hash and just taking top hash as prev hash
    @staticmethod
    def fill_with_dummies(dag, prev_hash, range):
        dummy_private = Private.generate()
        for i in range:
            dummy_time_offset = len(dag.blocks_by_number.get(i, []))
            block = BlockFactory.create_block_with_timestamp([prev_hash], BLOCK_TIME * i + dummy_time_offset)
            signed_block = BlockFactory.sign_block(block, dummy_private)
            dag.add_signed_block(i, signed_block)
            prev_hash = block.get_hash()
        
        return prev_hash
        
    @staticmethod
    def fill_with_dummies_and_skips(dag, prev_hash, range, indices_to_skip):
        dummy_private = Private.generate()
        for i in range:
            if i in indices_to_skip: continue
            dummy_time_offset = len(dag.blocks_by_number.get(i, []))
            block = BlockFactory.create_block_with_timestamp([prev_hash], BLOCK_TIME * i + dummy_time_offset)
            signed_block = BlockFactory.sign_block(block, dummy_private)
            dag.add_signed_block(i, signed_block)
            prev_hash = block.get_hash()
        
        return prev_hash
