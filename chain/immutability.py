from chain.dag import Dag, ChainIter
from chain.params import ZETA, ZETA_MAX, ZETA_MIN
from chain.skipped_block import SkippedBlock

CONSECUTIVE_CONST = 3

class Immutability:
    def __init__(self, dag: Dag):
        self.dag = dag

    def is_block_immutable(self, block_hash):
        return False

    def is_skip_immutable(self, skipped_block: SkippedBlock):
        return False

    def calculate_zeta(self, block_hash):
        import sys
        max_zeta = -sys.maxsize - 1  #TODO replace with reasonable number

        print("block hash", block_hash.hex()[0:6])

        tops = self.dag.get_top_blocks_hashes()
        for top in tops:
            zeta = 0
            iterator = ChainIter(self.dag, top)
            consecutive_skips = 0
            consecutive_blocks = 0
            print("top", top.hex()[0:6])
            for block in iterator:
                if block:
                    if block.get_hash() == block_hash:
                        if max_zeta < zeta:
                            max_zeta = zeta
                        continue

                if block:
                    consecutive_blocks += 1
                    consecutive_skips = 0
                else:
                    consecutive_skips += 1
                    consecutive_blocks = 0
                
                if consecutive_skips == CONSECUTIVE_CONST:
                    zeta -= 1
                    consecutive_skips = 0
                elif consecutive_blocks == CONSECUTIVE_CONST:
                    zeta += 1
                    consecutive_blocks = 0

            print("zeta is", zeta)

        print("max zeta is", max_zeta)
        return max_zeta

    def calculate_confirmations(self, block_hash):
        confirmations = [0]
        block_number = self.dag.get_block_number(block_hash)

        tops = self.dag.get_branches_for_timeslot_range(block_number + 1, block_number + ZETA + 1)

        for top in tops:
            branch_confirmations = 0
            chain_iter = ChainIter(self.dag, top)
            for block in chain_iter:
                if chain_iter.block_number == block_number: #if we counted enough
                    if block.get_hash() == block_hash: #if we counted on the branch including target block
                        confirmations.append(branch_confirmations)
                    break
                if block:
                    branch_confirmations += 1

        return max(confirmations)

    def calculate_skipped_block_confirmations(self, skipped_block):
        confirmations = self.calculate_confirmations(skipped_block.anchor_block_hash)
        #because anchor block is not counted in calculate_zeta we increase this value by one
        return confirmations + 1


