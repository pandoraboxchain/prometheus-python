import random
from chain.immutability import Immutability
from chain.dag import ChainIter
from chain.merged_chain import MergedChain
from chain.skipped_block import SkippedBlock

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

        longest_chain = sorted_chains[0]
        first_mutable_index = self.get_merging_point(longest_chain)
        active_merging_point = MergedChain(longest_chain[:first_mutable_index])
        merged_chain = MergedChain(longest_chain[:first_mutable_index])

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
            diffchain = active_merging_point.get_diff(chain)
            for i in range(len(diffchain)):
                block, is_mutable = self.get_block_from_chain(diffchain, i)
                if not is_mutable:
                    if not Merger.is_conflict(block, conflicts):
                        if not block in merged_chain:
                            merged_chain.append(block)
        
        for chain in sorted_chains:
            diffchain = active_merging_point.get_diff(chain)
            for i in range(len(diffchain)):
                block, is_mutable = self.get_block_from_chain(diffchain, i)
                if is_mutable:
                    if not Merger.is_conflict(block, conflicts):
                        if not block in merged_chain:
                            merged_chain.append(block)

        return merged_chain

    @staticmethod
    def is_conflict(block, conflicts):
        if SkippedBlock.is_skipped(block):
            return False

        return block.get_hash() in conflicts

    # returns first mutable block index
    def get_merging_point(self, chain):
        for i in range(len(chain)):
            _, is_mutable = self.get_block_from_chain(chain, i)
            if is_mutable:
                return i

    def get_block_from_chain(self, chain, index):
        block = chain[index]
        if not block:
            backstep_count = 0
            for j in range(index, len(chain)):
                if SkippedBlock.is_skipped(chain[j]):
                    backstep_count += 1
                else:
                    anchor_block_hash = chain[j].get_hash()
            block = SkippedBlock(anchor_block_hash, backstep_count)
        
        confirmations = chain.get_confirmations(index)
        if self.conf_req:
            needed_confirmations = self.conf_req.get_confirmation_requirement(block)
        else:
            needed_confirmations = 5

        is_mutable = confirmations < needed_confirmations

        return block, is_mutable

