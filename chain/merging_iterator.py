from chain.dag import ChainIter
from chain.merger import Merger
from chain.conflict_finder import ConflictFinder

# this gadget iterates till it meets block with multiple previous hashes
# then it performs recursive merge
# and iterates over merged blocks
# after merged blocks end it continues iterating over selected chain

class MergingIter:
    def __init__(self, dag, top_hash, conflict_finder=None, conf_req=None):
        self.chain_iter = ChainIter(dag, top_hash)
        self.merged_chain = []
        self.merger = Merger(dag, conf_req)
        self.finder = conflict_finder
        self.confirmation_requirement = conf_req

    def __iter__(self):
        return self

    # this method probably won't need to return block number, as merging iterator twists timeslot concept in a weird way
    def __next__(self):
        if self.merged_chain:
            return self.merged_chain.pop()

        block = self.chain_iter.next()

        if block and len(block.block.prev_hashes) > 1:
            prev_hashes = block.block.prev_hashes
            conflicts = []
            if self.finder:
                explicit_conflicts, candidate_groups = self.finder.find_conflicts_in_between(prev_hashes)
                resolved_candidate_conflicts = self.finder.filter_out_longest_chain_conflicts(candidate_groups, prev_hashes[0])
                conflicts = explicit_conflicts + resolved_candidate_conflicts
                
            self.merged_chain = self.merger.merge(prev_hashes, conflicts)
            self.merged_chain = self.merged_chain.filter_out_skipped_blocks() # TODO is it okay to omit skipped blocks in already fully merged chain?
            
            # overwrite chain iterator with next block after merge
            # this way when merged blocks end we can continue iterating further
            last_merged_block = self.merged_chain[0]
            self.chain_iter = ChainIter(self.chain_iter.dag, last_merged_block.get_hash())
            self.chain_iter.next() # immediately transfer to next block since last_merged was already popped from merged_chain
        
        return block
    
    def next(self):
        return self.__next__()