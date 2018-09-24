import random
from chain.immutability import Immutability
from chain.dag import ChainIter

class Merger:

    def __init__(self, dag):
        self.dag = dag

    # returns longest chain top hash and the rest of top block hashes
    def get_top_and_conflicts(self):
        top_blocks = list(self.dag.get_top_blocks().keys())
        conflicts = []
        if len(top_blocks) > 1:
            top = self.dag.get_longest_chain_top_block(top_blocks)
            number = self.dag.get_block_number(top)
            chains_intesect = False
            while number > 0 and not chains_intesect:
                for block in self.dag.blocks_by_number[number]:
                    block_hash = block.block.get_hash()
                    if not self.dag.is_ancestor(top, block_hash):
                        conflicts.append(block_hash)
                
                if len(self.dag.blocks_by_number[number]) > 1:
                    chains_intesect = True
                    prev_hashes = self.dag.blocks_by_number[number][0].block.prev_hashes
                    for block in self.dag.blocks_by_number[number]:
                        chains_intesect = chains_intesect and block.block.prev_hashes == prev_hashes

                number -= 1
        else:
            top = top_blocks[0]

        return top, conflicts
            top = top_blocks[0]

        return top, conflicts

    #determines hash of common ancestor of two chains using first-only children iteration approach
    def get_common_ancestor(self, first_chain, second_chain):
        first_blocks = []
        second_blocks = []
        first_iter = ChainIter(self.dag, first_chain)
        second_iter = ChainIter(self.dag, second_chain)
        while True: #TODO some sane alternative algorithm
            first_chain_block = first_iter.next()
            if first_chain_block:
                block_hash = first_chain_block.get_hash()
                if block_hash in second_blocks:
                    return block_hash
                first_blocks.append(block_hash)
            second_chain_block = second_iter.next()
            if second_chain_block:
                block_hash = second_chain_block.get_hash()
                if block_hash in first_blocks:
                    return block_hash
                second_blocks.append(block_hash)
