from chain.dag import Dag, ChainIter
from chain.params import ZETA, ZETA_MIN, ZETA_MAX
from chain.skipped_block import SkippedBlock

ZETA_CHANGE_CONST = 3

class ConfirmationRequirement:
    def __init__(self, dag: Dag):
        self.dag = dag
        dag.subscribe_to_new_block_notification(self)
        genesis_hash = dag.genesis_block().get_hash()
        self.blocks = {genesis_hash : ZETA_MAX}

    def on_new_block_added(self, block):
        block_hash = block.get_hash()

        #TODO think if attack is possible here
        req = self.choose_next_best_requirement(block_hash)
        if req == -1:
            closest_prev_hash, skip_count = self.choose_shortest_skip(block_hash)
            zeta_decrease = skip_count // ZETA_CHANGE_CONST
            prev_zeta = self.get_confirmation_requirement(closest_prev_hash)
            req = prev_zeta - zeta_decrease

        current_zeta = max(ZETA_MIN, min(req, ZETA_MAX))

        self.blocks[block.get_hash()] = current_zeta

    def on_timeslot_changed(self, prev_timeslot, current_timeslot):
        pass

    def get_confirmation_requirement(self, block):
        if isinstance(block, SkippedBlock):
            return self.get_skip_confirmation_requirement(block)
        assert block in self.blocks
        return self.blocks[block]

    def get_skip_confirmation_requirement(self, skipped_block):
        req = 0
        anchor_block_hash = skipped_block.anchor_block_hash
        assert anchor_block_hash in self.blocks
        anchor_block_requirement = self.blocks[anchor_block_hash]
        _, shortest_gap_before_anchor = self.choose_shortest_skip(anchor_block_hash)
        # full_rounds_count = shortest_gap_before_anchor // ZETA_CHANGE_CONST * ZETA_CHANGE_CONST
        leftover = shortest_gap_before_anchor % ZETA_CHANGE_CONST
        if skipped_block.backstep_count <= leftover:
            req = anchor_block_requirement
        else:
            backstep_count = skipped_block.backstep_count - leftover
            zeta_increase = (backstep_count - 1) // ZETA_CHANGE_CONST
            req = anchor_block_requirement + zeta_increase + 1 # plus 1 because we have already one round back
        
        req = max(ZETA_MIN, min(req, ZETA_MAX))
        return req

    def choose_shortest_skip(self, block_hash):
        prev_hashes = self.dag.get_links(block_hash)
        closest_prev_hash = prev_hashes[0]
        block_number = self.dag.get_block_number(block_hash)
        prev_block_number = self.dag.get_block_number(closest_prev_hash)
        shortest_skip = block_number - prev_block_number - 1
        for prev_hash in prev_hashes[1:]:
            prev_block_number = self.dag.get_block_number(prev_hash)
            skip_count = block_number - prev_block_number - 1
            if skip_count < shortest_skip:
                shortest_skip = skip_count
                closest_prev_hash = prev_hash
        
        return closest_prev_hash, shortest_skip

    # chooses maximum previous zeta
    # considers possibility of zeta to be increased
    def choose_next_best_requirement(self, block_hash):
        max_req = -1
        block_number = self.dag.get_block_number(block_hash)
        for prev_hash in self.dag.get_links(block_hash):
            prev_block_number = self.dag.get_block_number(prev_hash)
            if block_number - prev_block_number > 1: continue # don't consider interrupted  sequences
            req = self.get_confirmation_requirement(prev_hash)
            should_be_increased = self.recursive_sequence_finder(prev_hash, req, 1)
            if should_be_increased:
                req += 1
            if req > max_req:
                max_req = req
        
        return max_req

    # finds if there is a sequence of uninterrupted same value requirements
    # returns True if next value should be increased by one
    def recursive_sequence_finder(self, block_hash, initial_req_value, lookback_count):
        block_number = self.dag.get_block_number(block_hash)
        for prev_hash in self.dag.get_links(block_hash):
            prev_block_number = self.dag.get_block_number(prev_hash)
            if block_number - prev_block_number > 1: continue  # don't count interrupted  sequences    
            prev_req = self.get_confirmation_requirement(prev_hash)
            if prev_req == initial_req_value:
                if lookback_count == ZETA_CHANGE_CONST - 1: # minus one here because our initial block is already known
                    return True
                if self.recursive_sequence_finder(prev_hash, initial_req_value, lookback_count + 1):
                    return True
            
        return False
