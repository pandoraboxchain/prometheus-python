from insentives.hard import HardPenalty

class PenaltyDoubleBlock():

    def get_penalty(self, dag, double_block_transaction):
        validator = double_block_transaction.validator
        size = validator.stake*1
        return HardPenalty(size)
