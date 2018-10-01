from chain.dag import ChainIter
from chain.immutability import Immutability
from chain.params import ZETA

class FlatChain(list):

    def __init__(self, other):
        for i in other:
            self.append(i)

    @staticmethod
    def from_top_hash(dag, top_hash):
        flat_chain = []
        chain_iter = ChainIter(dag, top_hash)
        for block in chain_iter:
            if block:
                flat_chain.append(block)
            else:
                flat_chain.append(None)

        return FlatChain(list(reversed(flat_chain)))

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
        return FlatChain(another[dpoint:])

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