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
        tops = self.dag.get_top_blocks_hashes()
        sizes = [self.dag.calculate_chain_length(top) for top in tops]
        dict_sizes = dict(enumerate(sizes))
        deterministic_ordering = []
        while dict_sizes:
            m = max(dict_sizes.values())
            indexes = [key for key,value in dict_sizes.items() if value==m]
            if len(indexes) == 1:
                dict_sizes.pop(indexes[0])
                deterministic_ordering.append(indexes[0])
            else:
                for item in indexes:
                    dict_sizes.pop(item)
                random.shuffle(indexes)
                deterministic_ordering += indexes

        longest_chain = tops[deterministic_ordering[0]]
        immutability = Immutability(self.dag)
        longest_chain_mutable_part = immutability.get_mutable_part_of_chain(longest_chain)
        # active_merged_point = Chain(active[:merging_point])
        merged_chain = []

        for doi in deterministic_ordering[1:]:
            diffchain = self.get_difference(longest_chain_mutable_part, tops[doi])
            im_chain = diffchain.get_all_immutable()
            if im_chain:
                for im in im_chain:
                    if not im.is_empty:
                        if not merged_chain.find_block_by_identifier(im.identifier):
                            merged_chain.append(im)
        
        for doi in deterministic_ordering:
            diffchain = active_merged_point.get_diff(chains[doi])[1]
            m_chain = diffchain.get_all_mutable()
            if m_chain:
                for m in m_chain:
                    if not m.is_empty:
                        if not merged_chain.find_block_by_identifier(m.identifier):
                            merged_chain.append(m)

        return {
            "deterministic_ordering": deterministic_ordering,
            "merged_chain": merged_chain,
        }

