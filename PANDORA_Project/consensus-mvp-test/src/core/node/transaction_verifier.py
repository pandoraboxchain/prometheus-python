from core.transaction.stake_transaction import PenaltyTransaction
from core.transaction.secret_sharing_transactions import PrivateKeyTransaction


class TransactionVerifier:
    def __init__(self, dag):
        self.dag = dag

    @staticmethod
    def check_if_valid(transaction):
        if isinstance(transaction, PrivateKeyTransaction):  # do not accept to mempool, because its block only tx
            return False
        elif isinstance(transaction, PenaltyTransaction):  # do not accept to mempool, because its block only tx
            return False
        return True   