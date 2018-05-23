class Penalty():
    pass

class PenaltyPrevBlock():

    def get_penalty(self, dag, block_obj, block_sub):
        if block_obj==None:
            return 2

class PenaltyGossipAboutMe():

    def get_penalty(self, dag, block_obj, block_sub):
        return block_sub.gossips_about_block().get_size_of_negative_gosssip()*1

class PanaltyByBlock():
    pass

class PenaltyBlockList():
    pass
