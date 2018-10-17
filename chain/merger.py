import random
from chain.immutability import Immutability
from chain.dag import ChainIter
from chain.MergedChain import MergedChain

class Merger:

    def __init__(self, dag):
        self.dag = dag

    # TODO @deprecated ?
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

    # TODO may be move to DAG ----> ?
    def get_common_ancestor(self, first_chain, second_chain):
        first_blocks = []
        second_blocks = []
        first_iter = ChainIter(self.dag, first_chain)
        second_iter = ChainIter(self.dag, second_chain)
        while True: # TODO sane exit condition
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

    # TODO may be move to DAG ----> ?
    # returns part of of second chain where they diverge
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

    # done in deterministic manner, should yield exact same result on every node
    # returns indexes 
    @staticmethod
    def sort_deterministically(sizes):
        dict_sizes = dict(enumerate(sizes))
        sorted_dict = sorted(dict_sizes.items(), key=lambda kv: kv[1], reverse=True)
        sorted_keys = [key for key,value in sorted_dict]
        return sorted_keys
        
    def merge(self, tops):
        common_ancestor = self.dag.get_multiple_common_ancestor(tops)
        chains = [MergedChain.flatten_with_merge(self.dag, self, top, common_ancestor) for top in tops]
        sizes = [chain.get_chain_size() for chain in chains]
        deterministic_order = Merger.sort_deterministically(sizes)
        sorted_chains = [chains[index] for index in deterministic_order]

        active = sorted_chains[0]
        mp = active.get_merging_point()
        active_merged_point = MergedChain(active[:mp])
        merged_chain = MergedChain(active[:mp])

        # for chain in chains:
        #     chain_str = ""
        #     for block in chain:
        #         if block:
        #             chain_str += block.get_hash().hex()[0:6]
        #         else:
        #             chain_str += "None"
        #         chain_str += " "
        #     print(chain_str)

        for chain in sorted_chains[1:]:
            diffchain = active_merged_point.get_diff(chain)
            for block in diffchain:
                if block:
                    if not diffchain.is_block_mutable(block.get_hash()):
                        if not block in merged_chain:
                            merged_chain.append(block)
        
        for chain in sorted_chains:
            diffchain = active_merged_point.get_diff(chain)
            for block in diffchain:
                if block:
                    if diffchain.is_block_mutable(block.get_hash()):
                        if not block in merged_chain:
                            merged_chain.append(block)

        return merged_chain

