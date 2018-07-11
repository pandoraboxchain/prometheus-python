from transaction.stake_transaction import StakeHoldTransaction, PenaltyTransaction, StakeReleaseTransaction
from chain.dag import Dag, ChainIter
from chain.epoch import Epoch

class StakeManager():

    def __init__(self, epoch):
        self.epoch = epoch

    def get_stake_operations(self, epoch_hash):
        epoch_iter = ChainIter(self.epoch.dag, epoch_hash)
        
        stake_actions = []

        count = 0
        for block in epoch_iter:
            if block:
                for tx in block.block.system_txs:
                    if isinstance(tx, StakeHoldTransaction)
                    or isinstance(tx, StakeReleaseTransaction)
                    or isinstance(tx, PenaltyTransaction):
                        stake_actions.append(tx)

            count += 1
            if count == Epoch.get_duration():
                break

        return stake_actions
        