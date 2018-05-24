class Penalty():
    pass

class PenaltyPrevBlock():

    def get_penalty(self, dag, block_obj, block_sub):
        if block_obj==None:
            return 2
        else:
            return 0

class PenaltyGossipAboutMe():

    def get_penalty(self, dag, block_obj, block_sub):
        if block_obj==None:
            return block_sub.gossips_about_block().get_size_of_negative_gosssip()*1
        else:
            return 0

class PenaltyNotIncludingGossip():

    def get_penalty(self, dag, block_obj, block_sub):
        if block_obj==None:
            gossips = block_obj.gossips_about_block()
            counter = 0
            for g in gossips:
                if not (g.block_number > block_sub):
                    counter += 1
            return counter*4
        else:
            return 0

class PenaltyGossipPosition():

    def get_penalty(self, dag, block_obj, block_sub):
        if block_obj==None:
            gossips = block_obj.gossips_about_block().get_by_index(block_sub.number - block_obj.number)
            res = (gossips.block_number - block_obj.number) - 1
            return res*3
        else:
            return 0

class PanaltyByBlock():
    pass

class PenaltyBlockList():
    pass
