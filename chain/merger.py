import datetime
import operator
from crypto.keys import Keys
from chain.dag import Dag

class Merger():

    def __init__(self, dag):
        self.dag = dag

    def get_tops(self):
        return self.dag.get_top_blocks()
    
    def get_conflicts(self):
        top_blocks = list(self.dag.get_top_blocks().keys())
        conflicts = []
        if len(top_blocks) > 1:
            top = self.get_longest_chain_top_block(top_blocks)
            number = self.dag.get_block_number(top)
            conflict_count = len(self.dag.blocks_by_number[number]) - 1
            print("conflict_count", conflict_count)
            chains_intesect = False
            while number > 0 and not chains_intesect:
                for block in self.dag.blocks_by_number[number]:
                    block_hash = block.block.get_hash()
                    if not self.dag.is_ancestor(top, block_hash):
                        conflicts.append(block_hash)
                
                if len(self.dag.blocks_by_number[number]) > 1:
                    chains_intesect = True
                    prev_hashes = self.dag.blocks_by_number[number][0].block.prev_hashes
                    for block in self.dag.blocks_by_number[number]:
                        chains_intesect = chains_intesect and block.block.prev_hashes == prev_hashes

                number -= 1

        return conflicts

    def get_longest_chain_top_block(self, top_blocks):
        max_length = 0
        max_length_index = 0
        for i in range(0, len(top_blocks)):
            length = self.dag.calculate_chain_length(top_blocks[i])
            if length > max_length:
                max_length = length
                max_length_index = i

        return top_blocks[max_length_index]
            
            


        

    
    
