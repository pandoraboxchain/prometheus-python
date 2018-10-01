import random
from chain.immutability import Immutability
from chain.dag import ChainIter
from chain.flat_chain import FlatChain

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

    def get_common_ancestor(self, first_chain, second_chain):
        first_blocks = []
        second_blocks = []
        first_iter = ChainIter(self.dag, first_chain)
        second_iter = ChainIter(self.dag, second_chain)
        while True: #TODO sane exit condition
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

    #returns part of of second chain where they diverge
    def get_difference(self, first_chain, second_chain):
        common_ancestor = self.get_common_ancestor(first_chain, second_chain)

        chain_diff = []
        chain_iter = ChainIter(self.dag, second_chain)
        for block in chain_iter:
            if block:
                if block.get_hash() == common_ancestor:
                    break
            
            if block:
                chain_diff.append(block)
            else:
                chain_diff.append(None)

        return chain_diff
        
    def merge(self):
        chains = [FlatChain.from_top_hash(self.dag, top) for top in self.dag.get_top_blocks_hashes()]
        sizes = [chain.get_chain_size() for chain in chains]
        dict_sizes = dict(enumerate(sizes))
        deterministic_ordering = []
        while dict_sizes:
            m = max(dict_sizes.values())
            indexes = [key for key,value in dict_sizes.items() if value==m]
            if len(indexes)==1:
                dict_sizes.pop(indexes[0])
                deterministic_ordering.append(indexes[0])
            else:
                for item in indexes:
                    dict_sizes.pop(item)
                random.shuffle(indexes)
                deterministic_ordering += indexes

        immutability = Immutability(self.dag)
        active = chains[deterministic_ordering[0]]
        mp = active.get_merging_point(immutability)
        active_merged_point = FlatChain(active[:mp])
        merged_chain = FlatChain(active[:mp])


        for doi in deterministic_ordering[1:]:
            diffchain = active_merged_point.get_diff(chains[doi])
            for block in diffchain:
                if block:
                    if not immutability.is_block_mutable(block.get_hash()):
                        if not block in merged_chain:
                            merged_chain.append(block)
        
        for doi in deterministic_ordering:
            diffchain = active_merged_point.get_diff(chains[doi])
            for block in diffchain:
                if block:
                    if immutability.is_block_mutable(block.get_hash()):
                        if not block in merged_chain:
                            merged_chain.append(block)

        return merged_chain

