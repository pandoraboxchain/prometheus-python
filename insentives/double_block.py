class HardPenalty():

    def __init__(self, size):
        self.type = "hard"
        self.size = size

class PenaltyDoubleBlock():

    def get_penalty(self, dag, double_block_transaction):
        validator = double_block_transaction.validator
        size = validator.stake*1
        return HardPenalty(size)
