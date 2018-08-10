from chain.epoch import Round
from transaction.transaction import SplitRandomTransaction, PublicKeyTransaction, PrivateKeyTransaction
from transaction.transaction import StakeHoldTransaction, StakeReleaseTransaction, PenaltyTransaction

class Mempool():

    def __init__(self):
        self.public_keys = []
        self.private_keys = []
        self.stake_operations = []

    def add_transaction(self, tx):
        if isinstance(tx, SplitRandomTransaction):
            pass
        elif isinstance(tx, PublicKeyTransaction):
            self.public_keys.append(tx)
        elif isinstance(tx, PrivateKeyTransaction):
            self.private_keys.append(tx)
        elif isinstance(tx, StakeHoldTransaction) or\
             isinstance(tx, StakeReleaseTransaction):
            self.stake_operations.append(tx)
        else:
            assert False, "Can't add. Transaction type is unknown"

    # remove all occurences of given transaction
    def remove_transaction(self, tx):
        if isinstance(tx, SplitRandomTransaction):
            pass
        elif isinstance(tx, PublicKeyTransaction):
            self.public_keys = [a for a in self.public_keys if a.get_hash() != tx.get_hash()]
        elif isinstance(tx, PrivateKeyTransaction):
            self.private_keys = [a for a in self.private_keys if a.get_hash() != tx.get_hash()]
        elif isinstance(tx, StakeHoldTransaction) or\
             isinstance(tx, StakeReleaseTransaction):
            self.stake_operations = [a for a in self.stake_operations if a.get_hash() != tx.get_hash()]
        elif isinstance(tx, PenaltyTransaction): # should only be as part of the block
            pass
        else:
            assert False, "Can't remove. Transaction type is unknown"

    def get_transactions_for_round(self, round_type):
        if round_type == Round.RANDOM:
            return []
        elif round_type == Round.PUBLIC:
            public_keys = self.public_keys.copy()
            self.public_keys.clear()
            return public_keys
        elif round_type == Round.PRIVATE:
            private_keys = self.private_keys.copy()
            self.private_keys.clear()
            return private_keys
        else:
            assert False, "No known transactions for round"

    def remove_transactions(self, transactions):
        for tx in transactions:
            self.remove_transaction(tx)

    def remove_all_systemic_transactions(self):
        self.public_keys.clear()
        self.private_keys.clear()
        self.stake_operations.clear()

