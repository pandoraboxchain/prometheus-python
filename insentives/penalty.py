class Penalty():
    pass

PENALTY_PREV_BLOCK_CONST = 2


class PenaltyPrevBlock:

    def get_penalty(self, dag, block_obj, block_sub):
        if block_obj==None:
            return PENALTY_PREV_BLOCK_CONST
        else:
            return 0

PENALTY_GOSSIP_ABOUT_ME_CONTST = 1


class PenaltyGossipAboutMe:

    def get_penalty(self, dag, block_obj, block_sub):
        if block_obj==None:
            return block_sub.gossips_about_block().get_size_of_negative_gosssip()*PENALTY_GOSSIP_ABOUT_ME_CONTST
        else:
            return 0

PENALTY_NOT_INCLUDING_GOSSIP = 4


class PenaltyNotIncludingGossip:

    def get_penalty(self, dag, block_obj, block_sub):
        if block_obj==None:
            gossips = block_obj.gossips_about_block()
            counter = 0
            for g in gossips:
                if not (g.block_number > block_sub):
                    counter += 1
            return counter*PENALTY_NOT_INCLUDING_GOSSIP
        else:
            return 0

PENALTY_GOSSIP_POSITION = 3


class PenaltyGossipPosition:

    def get_penalty(self, dag, block_obj, block_sub):
        if block_obj==None:
            gossips = block_obj.gossips_about_block().get_by_index(block_sub.number - block_obj.number)
            res = (gossips.block_number - block_obj.number) - 1
            return res*PENALTY_GOSSIP_POSITION
        else:
            return 0

if PENALTY_PREV_BLOCK_CONST >= PENALTY_GOSSIP_POSITION:
    print("HALT!")

if PENALTY_NOT_INCLUDING_GOSSIP <= PENALTY_GOSSIP_POSITION:
    print("HALT!")

if PENALTY_GOSSIP_ABOUT_ME_CONTST >= PENALTY_PREV_BLOCK_CONST:
    print("HALT")


class PenaltyByBlock:
    pass


class PenaltyBlockList:
    pass
