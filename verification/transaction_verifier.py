from Crypto.Hash import SHA256
import struct
from transaction.transaction import PrivateKeyTransaction, PenaltyTransaction

class TransactionVerifier():
    def __init__(self, dag):
        self.dag = dag

    def check_if_valid(self, transaction):
        if isinstance(transaction, PrivateKeyTransaction): #do not accept to mempool, because its block only tx
            return False
        elif isinstance(transaction, PenaltyTransaction): #do not accept to mempool, because its block only tx
            return False
        return True   