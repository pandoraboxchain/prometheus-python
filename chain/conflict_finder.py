import random
from chain.dag import ChainIter


class ConflictFinder:

    def __init__(self, dag):
        self.dag = dag

    def find_conflicts(self, top_blocks):
        """ Method return one top hash in case of many tops and
            all conflict blocks till ancestor exclude chosen
            top hash and all top chain blocks hashes
            :param top_blocks: list of current top blocks
            :return: top - hash of top block in current chain
                     conflicts - ordered hash list of conflict blocks
        """
        all_conflicts = []
        # get ancestor
        ancestor_for_top = self.dag.get_common_ancestor(top_blocks)
        # get ancestor block number
        ancestor_block_number = self.dag.get_block_number(ancestor_for_top)

        # determinate current top
        top_block_hash = self.determinate_top(top_blocks, ancestor_for_top)
        # get chosen top bock number
        top_block_number = self.dag.get_block_number(top_block_hash)

        # append all conflicts by range from accessor to top block timeslot (include all blocks in top timeslot)
        for block_number in range(ancestor_block_number + 1, top_block_number + 1):
            all_conflicts.append(self.dag.blocks_by_number[block_number])

        # filter conflicts from determined top logical chin blocks
        conflicts_list = self.check_conflicts_for_determined_top(top_block_hash=top_block_hash,
                                                                 ancestor_for_top=ancestor_for_top,
                                                                 conflicts=all_conflicts)
        return top_block_hash, conflicts_list

    # ------------------------------------------------------------
    # internal methods
    # ------------------------------------------------------------
    def determinate_top(self, top_blocks, ancestor_for_top):
        """ Method return one top in case of many tops
            :param top_blocks: list of current top blocks
            :param ancestor_for_top: lower sampling limit
            :return: longest or random top hash
        """
        assert len(top_blocks) is not 0, 'Unable to determinate current top, tops is empty.'
        if len(top_blocks) > 1:  # determinate current top (if tops>1)
            top = self.get_longest_chain_top_block(top_blocks, ancestor_for_top)
        else:  # determinate current top (if tops=1)
            top = top_blocks[0]
        return top

    # returns longest chain and chooses randomly if there are equal length longest chains
    def get_longest_chain_top_block(self, top_blocks, ancestor_for_top):
        """ Method will shuffle current tops, check up length of every top,
            and return longest top from current tops by lower sampling limit ancestor_for_top
            :param top_blocks: list of current top blocks
            :param ancestor_for_top: lower sampling limit
            :return: longest or random top hash
        """
        randgen = random.SystemRandom()  # crypto secure random
        randgen.shuffle(top_blocks)  # randomly shuffle tops so same length chains won't be chosen deterministically

        max_length = 0
        max_length_index = 0
        for i in range(0, len(top_blocks)):
            length = len(self.get_top_chain_block_hashes(from_hash=top_blocks[i],
                                                         to_hash=ancestor_for_top))
            if length > max_length:
                max_length = length
                max_length_index = i
        return top_blocks[max_length_index]

    def check_conflicts_for_determined_top(self, top_block_hash, ancestor_for_top, conflicts):
        """ Method will cleanup all received conflicts and return conflicts
            with excluded selected top and top logical blocks
            :param top_block_hash: hash on determined block
            :param ancestor_for_top: ancestor (lower sampling limit)
            :param conflicts: current total list of conflicts
            :return: ready to use cleaned list of conflicts
        """
        conflicts_list_result = []  # result
        # make conflicts as list
        for conflict in conflicts:
            for block in conflict:
                conflicts_list_result.append(block)

        # get all block hashes for determined top
        top_chain_block_hashes = self.get_top_chain_block_hashes(from_hash=top_block_hash,
                                                                 to_hash=ancestor_for_top)
        conflicts_list_result_hashes = []
        for conflict in conflicts_list_result:
            conflicts_list_result_hashes.append(conflict.block.get_hash())

        for block_hash in top_chain_block_hashes:
            if block_hash:
                if block_hash in conflicts_list_result_hashes:
                    conflicts_list_result_hashes.remove(block_hash)

        return conflicts_list_result_hashes

    def get_top_chain_block_hashes(self, from_hash, to_hash):
        """ Method return list of logical block by block chain
            from hash to hash IN THE OPPOSITE DIRECTION (from current top to to_hash)
            :param from_hash: current top hash
            :param to_hash: any hash from chain
            :return: list of block hashes in logical sequences WITHOUT SKIPS
        """
        flat_chain = []
        chain_iter = ChainIter(self.dag, from_hash)
        block = chain_iter.next()
        block_hash = block.get_hash()
        while block_hash != to_hash:
            if block:
                flat_chain.append(block.get_hash())

            block = chain_iter.next()
            if block:
                block_hash = block.get_hash()
            else:
                block_hash = None

        flat_chain.append(self.dag.blocks_by_hash[to_hash])

        return list(reversed(flat_chain))



