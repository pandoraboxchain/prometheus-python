from chain.merger import Merger


class ConflictFinder:

    def __init__(self, dag):
        self.dag = dag
        self.merger = Merger(dag)

    def find_conflicts(self, top_blocks):
        conflicts = []
        # get ancestor
        ancestor_for_top = self.merger.get_multiple_common_ancestor(top_blocks)
        # get ancestor block number
        ancestor_block_number = self.dag.get_block_number(ancestor_for_top)

        # determinate current top
        top_block_hash = self.determinate_top(top_blocks)
        # get chosen top bock number
        top_block_number = self.dag.get_block_number(top_block_hash)

        for block_number in range(ancestor_block_number + 1, top_block_number):
            conflicts.append(self.dag.blocks_by_number[block_number])

        return top_block_hash, conflicts

    # ------------------------------------------------------------
    # internal methods
    # ------------------------------------------------------------
    def determinate_top(self, top_blocks):
        assert len(top_blocks) is not 0, 'Unable to determinate current top, tops is empty.'
        if len(top_blocks) > 1:  # determinate current top (if tops>1)
            top = self.dag.get_longest_chain_top_block(top_blocks)
        else:  # determinate current top (if tops=1)
            top = top_blocks[0]
        return top


