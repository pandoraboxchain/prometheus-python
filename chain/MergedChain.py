from chain.dag import ChainIter
from chain.immutability import Immutability
from chain.params import ZETA

# from chain.merger import Merger #it should be cyclic dependency, so I just  


# TODO possibly deprecated
class MergedChain(list):

    def __init__(self, other):
        for i in other:
            self.append(i)

    # this method flattens chain and merges it recursively if its needed
    # it should be possible to merge already merged chains
    @staticmethod
    def flatten_with_merge(dag, merger, from_hash, to_hash):
        flat_chain = []
        chain_iter = ChainIter(dag, from_hash)
        block = chain_iter.next()
        block_hash = block.get_hash()
        while block_hash != to_hash:
            if not block:
                flat_chain.append(None)
            else:
                flat_chain.append(block)
                if len(block.block.prev_hashes) > 1:
                    merge_chain = merger.merge(block.block.prev_hashes)
                    flat_chain += list(reversed(merge_chain))
                    chain_iter = ChainIter(dag, merge_chain[0].get_hash())
                    chain_iter.next() # immediately transfer to next block because this one is already in chain

            block = chain_iter.next()
            if block: block_hash = block.get_hash()
            else: block_hash = None

        flat_chain.append(dag.blocks_by_hash[to_hash])

        return MergedChain(list(reversed(flat_chain)))

    def get_chain_size(self):
        count = 0
        for item in self:
            if item:
                count += 1
        return count

    def get_diff(self, another):
        i = 0
        stop = False
        while i != min(len(self), len(another)) and (not stop):
            stop = self[i] != another[i]
            if not stop:
                i+=1
        dpoint = i
        return MergedChain(another[dpoint:])

    def get_merging_point(self):
        i = 0
        stop = False
        while i != len(self) and (not stop):
            stop = self.is_slot_mutable(i)
            if not stop:
                i+=1
        mpoint = i
        return mpoint

    def is_slot_mutable(self, timeslot_num):
        confirmations = 0
        for i in range(timeslot_num, len(self)):
            if self[i]:
                confirmations += 1
        return confirmations < ZETA
    
    def is_block_mutable(self, block_hash):
        for i in range(len(self)):
            block = self[i]
            if block:
                if block.get_hash() == block_hash:
                    return self.is_slot_mutable(i)
        assert False, "Can't find block with hash %r to calculate its immutability" % block_hash.hex()