from chain.dag import Dag, ChainIter
from chain.params import ZETA

CONSECUTIVE_CONST = 3


class Immutability:
    def __init__(self, dag: Dag, confirmation_requirement):
        self.dag = dag
        self.confimation_requirement = confirmation_requirement 

    def is_block_immutable(self, block_hash):
        confirmation_req_value = self.confimation_requirement.get_confirmation_requirement(block_hash)
        confirmations = self.calculate_confirmations(block_hash)
        return confirmations >= confirmation_req_value

    #TODO include gossips into confirmation calculation
    def calculate_confirmations(self, block_hash):
        confirmations = [0]
        block_number = self.dag.get_block_number(block_hash)

        tops = self.dag.get_branches_for_timeslot_range(block_number + 1, block_number + ZETA + 1)

        for top in tops:
            branch_confirmations = 0
            chain_iter = ChainIter(self.dag, top)
            for block in chain_iter:
                if chain_iter.block_number == block_number:  # if we counted enough
                    if block.get_hash() == block_hash:  # if we counted on the branch including target block
                        confirmations.append(branch_confirmations)
                    break
                if block:
                    branch_confirmations += 1

        return max(confirmations)

    #TODO should this be used?
    def calculate_skipped_block_confirmations(self, skipped_block):
        confirmations = self.calculate_confirmations(skipped_block.anchor_block_hash)
        # because anchor block is not counted in calculate_zeta we increase this value by one
        return confirmations + 1


