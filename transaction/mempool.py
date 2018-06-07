from chain.epoch import Round
from transaction.transaction import CommitRandomTransaction, RevealRandomTransaction

class Mempool():
    transactions = []
    commits = []
    reveals = []

    def add_transaction(self, tx):
        if isinstance(tx, CommitRandomTransaction):
            self.commits.append(tx)
        elif isinstance(tx, RevealRandomTransaction):
            self.reveals.append(tx)

    def get_transactions_for_round(self, round_type):
        if round_type == Round.PUBLIC:
            commits = self.commits.copy()
            self.commits.clear();
            return commits
        elif round_type == Round.RANDOM:
            reveals = self.reveals.copy()
            self.reveals.clear()
            return reveals
        else:
            return []

