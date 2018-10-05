from chain.dag import ChainIter
from chain.merger import Merger

# this gadget iterates till it meets block with multiple previous hashes
# then it performs recursive merge
# and iterates over merged blocks
# after merged blocks end it continues iterating over selected chain

class MergingIter:
    def __init__(self, dag, top_hash):
        self.chain_iter = ChainIter(dag, top_hash)
        self.merged_chain = []
        self.merger = Merger(dag)

    def __iter__(self):
        return self

    # this method probably won't need to return block number, as merging iterator twists timeslot concept in a weird way
    def __next__(self):
        if self.merged_chain:
            return self.merged_chain.pop()

        block = self.chain_iter.next()

        if len(block.block.prev_hashes) > 1:
            self.merged_chain = self.merger.merge(block.block.prev_hashes)
            
            # overwrite chain iterator with next block after merge
            # this way when merged blocks end we can continue iterating further
            last_merged_block = self.merged_chain[0]
            self.chain_iter = ChainIter(self.chain_iter.dag, last_merged_block)
        
        return block
    
    def next(self):
        return self.__next__()