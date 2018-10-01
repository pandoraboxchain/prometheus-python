from chain.dag import ChainIter
from chain.immutability import Immutability

class FlatChain(list):

    def __init__(self, other):
        self = other

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
        return another[dpoint:]

    def get_merging_point(self, immutability):
        i = 0
        stop = False
        while i != len(self) and (not stop):
            stop = imm.is_block_mutable(self[i])
            if not stop:
                i+=1
        mpoint = i
        return mpoint
