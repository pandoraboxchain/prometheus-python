from chain.epoch import Round
from transaction.transaction import SplitRandomTransaction, PublicKeyTransaction, PrivateKeyTransaction
from transaction.transaction import PenaltyTransaction

class Mempool():

    def __init__(self):
        self.split_randoms = []
        self.public_keys = []
        self.private_keys = []

    def add_transaction(self, tx):
        if isinstance(tx, SplitRandomTransaction):
            self.split_randoms.append(tx)
        elif isinstance(tx, PublicKeyTransaction):
            self.public_keys.append(tx)
        elif isinstance(tx, PrivateKeyTransaction):
            self.private_keys.append(tx)
        else:
            assert False, "Can't add. Transaction type is unknown"

    # remove all occurences of given transaction
    def remove_transaction(self, tx):
        if isinstance(tx, SplitRandomTransaction):
            self.split_randoms = [a for a in self.split_randoms if a.get_hash() != tx.get_hash()]
        elif isinstance(tx, PublicKeyTransaction):
            self.public_keys = [a for a in self.public_keys if a.get_hash() != tx.get_hash()]
        elif isinstance(tx, PrivateKeyTransaction):
            self.private_keys = [a for a in self.private_keys if a.get_hash() != tx.get_hash()]
        elif isinstance(tx, PenaltyTransaction):
            pass
        else:
            assert False, "Can't remove. Transaction type is unknown"

    def get_transactions_for_round(self, round_type):
        if round_type == Round.RANDOM:
            split_randoms = self.split_randoms.copy()
            self.split_randoms.clear()
            return split_randoms
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
        self.split_randoms.clear()
        self.public_keys.clear()
        self.private_keys.clear()

