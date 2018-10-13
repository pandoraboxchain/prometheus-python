from chain.dag import Dag, ChainIter
from chain.params import ZETA, ZETA_MIN, ZETA_MAX

ZETA_CHANGE_CONST = 3

class ConfirmationRequirement:
    def __init__(self, dag: Dag):
        self.dag = dag
        dag.subscribe_to_new_block_notification(self)
        genesis_hash = dag.genesis_block().get_hash()
        self.blocks = {genesis_hash : ZETA_MAX}

    def on_new_block_added(self, block):
        block_hash = block.get_hash()

        # this_block_confirmation_requirement = None
        # for prev_hash in block.prev_hashes:
        #     if prev_hash in self.tops:
        #         prev_top_conf_req = self.tops[prev_hash]
        #         del self.tops[prev_hash]
        #         if (not this_block_confirmation_requirement) or \
        #             (prev_top_conf_req > this_block_conf_req): #TODO make sure if we need to choose highest one
        #             this_block_conf_req = prev_top_conf_req
        
        # if this_block_confirmation_requirement != None:
        #     self.tops[block_hash] = this_block_confirmation_requirement

        prev_block_hash = block.block.prev_hashes[0]
        block_number = self.dag.get_block_number(block_hash)
        prev_block_number = self.dag.get_block_number(prev_block_hash)

        #TODO think if attack is possible here
        skip_count = block_number - prev_block_number
        zeta_decrease = skip_count // ZETA_CHANGE_CONST
        prev_zeta = self.get_confirmation_requirement(prev_block_hash)
        current_zeta = prev_zeta - zeta_decrease

        # if skip_count == 0:

        current_zeta = max(ZETA_MIN, min(current_zeta, ZETA_MAX))

        # for block in iterator:
            # if block:
                # consecutive_blocks += 1
            # else:
                # consecutive_skips += 1
            # 
            # count += 1
            # if count == LOOKBACK_CONST:
                # break

        self.blocks[block.get_hash()] = current_zeta

    def on_timeslot_changed(self, prev_timeslot, current_timeslot):
        pass

    def get_confirmation_requirement(self, block_hash):
        assert block_hash in self.blocks
        return self.blocks[block_hash]

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
            print("looking at", prev_hash.hex()[0:6], "its req is", prev_req, "count", lookback_count)
            if prev_req == initial_req_value:
                if lookback_count == ZETA_CHANGE_CONST - 1: # minus one here because our initial block is already known
                    return True
                if self.recursive_sequence_finder(prev_hash, initial_req_value, lookback_count + 1):
                    return True
            
        return False
