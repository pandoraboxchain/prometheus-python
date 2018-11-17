from chain.dag import ChainIter
from chain.immutability import Immutability
from chain.params import ZETA
from chain.skipped_block import SkippedBlock
from transaction.gossip_transaction import PositiveGossipTransaction, NegativeGossipTransaction

# from chain.merger import Merger #it should be cyclic dependency, so I just  


# TODO possibly deprecated
class MergedChain(list):

    def __init__(self, other):
        for i in other:
            self.append(i)

    # this method flattens chain and merges it recursively if its needed
    # it should be possible to merge already merged chains
    @staticmethod
    def flatten_with_merge(merger, from_hash, to_hash):
        flat_chain = []
        chain_iter = ChainIter(merger.dag, from_hash)
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
                    chain_iter = ChainIter(merger.dag, merge_chain[0].get_hash())
                    chain_iter.next() # immediately transfer to next block because this one is already in chain

            block = chain_iter.next()
            if block: block_hash = block.get_hash()
            else: block_hash = None

        flat_chain.append(merger.dag.blocks_by_hash[to_hash])

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

    def get_confirmations(self, timeslot_num):
        confirmations = 0
        selected_block = self[timeslot_num]
        for i in range(timeslot_num, len(self)):
            block = self[i]
            is_skipped = not block or isinstance(block, SkippedBlock)
            if not is_skipped:
                for tx in block.block.system_txs:
                    if selected_block:
                        if isinstance(tx, PositiveGossipTransaction):
                            if tx.block_hash == selected_block.get_hash():
                                confirmations += 1
                    else:
                        if isinstance(tx, NegativeGossipTransaction):
                            if tx.number_of_block == timeslot_num:
                                confirmations += 1
        
        return confirmations

    def filter_out_skipped_blocks(self):
        return MergedChain(filter(lambda block: not SkippedBlock.is_skipped(block), self))
        # sds = 4
        # for i in range(len(self)):
        #     if SkippedBlock.is_skipped(self[i]):
        #         del self[i]

    def debug_print_block_numbers(self, dag):
        print("Debug print block numbers in merged chain")
        for block in self:
            if not SkippedBlock.is_skipped(block):
                block_hash = block.get_hash()
                print(block_hash.hex()[0:6], "number", dag.get_block_number(block_hash))