from Crypto.Hash import SHA256
import struct
from transaction.transaction import CommitRandomTransaction, RevealRandomTransaction

class TransactionVerifier():
    def __init__(self, dag):
        self.dag = dag

    def check_if_valid(self, transaction):
        if isinstance(transaction, RevealRandomTransaction):
            return True
        return True     