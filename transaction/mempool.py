from chain.params import Round
from transaction.gossip_transaction import NegativeGossipTransaction, \
                                           PositiveGossipTransaction, \
                                           PenaltyGossipTransaction
from transaction.secret_sharing_transactions import SplitRandomTransaction, PublicKeyTransaction, PrivateKeyTransaction
from transaction.stake_transaction import StakeHoldTransaction, StakeReleaseTransaction, PenaltyTransaction
from transaction.commit_transactions import CommitRandomTransaction, RevealRandomTransaction


class Mempool:

    def __init__(self):
        self.public_keys = []
        self.stake_operations = []
        self.commits = []
        self.reveals = []
        self.shares = []
        self.gossips = []

    def add_transaction(self, tx):
        if isinstance(tx, PublicKeyTransaction):
            self.public_keys.append(tx)
        elif isinstance(tx, StakeHoldTransaction) or\
                isinstance(tx, StakeReleaseTransaction):
            self.stake_operations.append(tx)
        elif isinstance(tx, CommitRandomTransaction):
            self.commits.append(tx)
        elif isinstance(tx, RevealRandomTransaction):
            self.reveals.append(tx)
        elif isinstance(tx, SplitRandomTransaction):
            self.shares.append(tx)
        elif isinstance(tx, NegativeGossipTransaction):
            self.gossips.append(tx)
        elif isinstance(tx, PositiveGossipTransaction):
            self.gossips.append(tx)
        elif isinstance(tx, PenaltyGossipTransaction):
            self.gossips.append(tx)
        else:
            assert False, "Can't add. Transaction type is unknown or should not be added to mempool"

    # remove all occurences of given transaction
    def remove_transaction(self, tx):
        if isinstance(tx, PrivateKeyTransaction) or \
               isinstance(tx, PenaltyTransaction):  # should only be as part of the block
                pass
        elif isinstance(tx, PublicKeyTransaction):
            self.public_keys = [a for a in self.public_keys if a.get_hash() != tx.get_hash()]
        elif isinstance(tx, StakeHoldTransaction) or isinstance(tx, StakeReleaseTransaction):
            self.stake_operations = [a for a in self.stake_operations if a.get_hash() != tx.get_hash()]
        elif isinstance(tx, CommitRandomTransaction):
            self.commits = [a for a in self.commits if a.get_hash() != tx.get_hash()]
        elif isinstance(tx, RevealRandomTransaction):
            self.reveals = [a for a in self.reveals if a.get_hash() != tx.get_hash()]
        elif isinstance(tx, SplitRandomTransaction):
            self.shares = [a for a in self.shares if a.get_hash() != tx.get_hash()]

        elif isinstance(tx, NegativeGossipTransaction):
            self.shares = [a for a in self.gossips if a.get_hash() != tx.get_hash()]
        elif isinstance(tx, PositiveGossipTransaction):
            self.shares = [a for a in self.gossips if a.get_hash() != tx.get_hash()]
        elif isinstance(tx, PenaltyGossipTransaction):
            self.shares = [a for a in self.gossips if a.get_hash() != tx.get_hash()]
        else:
            assert False, "Can't remove. Transaction type is unknown"

    def get_transactions_for_round(self, round_type):
        if round_type == Round.PRIVATE or \
           round_type == Round.FINAL:
            return []
        elif round_type == Round.PUBLIC:
            public_keys = self.public_keys.copy()
            self.public_keys.clear()
            return public_keys
        elif round_type == Round.COMMIT:
            commits = self.commits.copy()
            self.commits.clear()
            return commits
        elif round_type == Round.REVEAL:
            reveals = self.reveals.copy()
            self.reveals.clear()
            return reveals
        elif round_type == Round.SECRETSHARE:
            shares = self.shares.copy()
            self.shares.clear()
            return shares
        else:
            assert False, "No known transactions for round"

    def pop_round_system_transactions(self, round):
        txs = self.get_transactions_for_round(round)
        txs += self.gossips
        return txs

    def remove_transactions(self, transactions):
        for tx in transactions:
            self.remove_transaction(tx)

    def remove_all_systemic_transactions(self):
        self.public_keys.clear()
        self.shares.clear()
        self.stake_operations.clear()
        self.commits.clear()
        self.reveals.clear()
        self.gossips.clear()

