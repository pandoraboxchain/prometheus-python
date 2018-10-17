from chain.flat_chain import FlatChain


class ConflictFinder:

    def __init__(self, dag):
        self.dag = dag

    def find_conflicts(self, top_blocks):
        all_conflicts = []
        # get ancestor
        ancestor_for_top = self.dag.get_multiple_common_ancestor(top_blocks)
        # get ancestor block number
        ancestor_block_number = self.dag.get_block_number(ancestor_for_top)

        # determinate current top
        top_block_hash = self.determinate_top(top_blocks)
        # get chosen top bock number
        top_block_number = self.dag.get_block_number(top_block_hash)

        # append all conflicts by range from accessor to top block timeslot number
        for block_number in range(ancestor_block_number + 1, top_block_number):
            all_conflicts.append(self.dag.blocks_by_number[block_number])

        # filter conflicts from determined top logical chin blocks
        conflicts_list = self.check_conflicts_for_determined_top(top_block_number=top_block_number,
                                                                 top_block_hash=top_block_hash,
                                                                 ancestor_for_top=ancestor_for_top,
                                                                 conflicts=all_conflicts)
        return top_block_hash, conflicts_list

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

    def check_conflicts_for_determined_top(self,
                                           top_block_number,
                                           top_block_hash,
                                           ancestor_for_top,
                                           conflicts):
        # сделать проще, убрать весь выбранный топ чейн на фильтрации и постараться обойтись только хешами
        conflicts_list_result = []  # result
        top_blocks_by_number = self.dag.blocks_by_number[top_block_number]
        block_last_timeslot = []
        for block in top_blocks_by_number:
            if block.get_hash() != top_block_hash:
                # add conflict blocks from last top timeslot
                block_last_timeslot.append(block)
        conflicts.append(block_last_timeslot)

        # make conflicts as list
        for conflict in conflicts:
            for block in conflict:
                conflicts_list_result.append(block)

        # use flatten_with_merge from FlatChain
        top_chain_block_hashes = FlatChain.get_flatten_by_block_hash(dag=self.dag,
                                                                     from_hash=top_block_hash,
                                                                     to_hash=ancestor_for_top)
        conflicts_list_result_hashes = []
        for conflict in conflicts_list_result:
            conflicts_list_result_hashes.append(conflict.block.get_hash())

        for block in top_chain_block_hashes:
            if block:
                block_hash = block.get_hash()
                if block_hash in conflicts_list_result_hashes:
                    conflicts_list_result_hashes.remove(block_hash)

        return conflicts_list_result_hashes


