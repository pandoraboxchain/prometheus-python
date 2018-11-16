import random
from chain.immutability import Immutability
from chain.dag import ChainIter
from chain.merged_chain import MergedChain

class Merger:

    def __init__(self, dag, conf_req=None):
        self.dag = dag
        self.conf_req = conf_req

    # done in deterministic manner, should yield exact same result on every node
    # returns indexes 
    @staticmethod
    def sort_deterministically(sizes):
        dict_sizes = dict(enumerate(sizes))
        sorted_dict = sorted(dict_sizes.items(), key=lambda kv: kv[1], reverse=True)
        sorted_keys = [key for key,value in sorted_dict]
        return sorted_keys
        
    def merge(self, tops, conflicts=[]):
        common_ancestor = self.dag.get_common_ancestor(tops)
        chains = [MergedChain.flatten_with_merge(self, top, common_ancestor) for top in tops]
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
                    block_hash = block.get_hash()
                    if block_hash not in conflicts:
                        if not diffchain.is_block_mutable(block.get_hash()):
                            if not block in merged_chain:
                                merged_chain.append(block)
        
        for chain in sorted_chains:
            diffchain = active_merged_point.get_diff(chain)
            for block in diffchain:
                if block:
                    block_hash = block.get_hash()
                    if block_hash not in conflicts:
                        if diffchain.is_block_mutable(block.get_hash()):
                            if not block in merged_chain:
                                merged_chain.append(block)

        return merged_chain

