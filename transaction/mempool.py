from chain.params import Round
from transaction.gossip_transaction import NegativeGossipTransaction, \
                                           PositiveGossipTransaction, \
                                           PenaltyGossipTransaction
from transaction.secret_sharing_transactions import SplitRandomTransaction, PublicKeyTransaction, PrivateKeyTransaction
from transaction.stake_transaction import StakeHoldTransaction, StakeReleaseTransaction, PenaltyTransaction
from transaction.commit_transactions import CommitRandomTransaction, RevealRandomTransaction
from transaction.payment_transaction import PaymentTransaction

class Mempool:

    def __init__(self):
        self.public_keys = {}
        self.stake_operations = {}
        self.commits = {}
        self.reveals = {}
        self.shares = {}
        self.gossips = {}
        self.payments = {}

    def add_transaction(self, tx):
        if isinstance(tx, PublicKeyTransaction):
            self.public_keys[tx.get_hash()] = tx
        elif isinstance(tx, StakeHoldTransaction) or\
                isinstance(tx, StakeReleaseTransaction):
            self.stake_operations[tx.get_hash()] = tx
        elif isinstance(tx, CommitRandomTransaction):
            self.commits[tx.get_hash()] = tx
        elif isinstance(tx, RevealRandomTransaction):
            self.reveals[tx.get_hash()] = tx
        elif isinstance(tx, SplitRandomTransaction):
            self.shares[tx.get_hash()] = tx
        elif isinstance(tx, NegativeGossipTransaction):
            self.gossips[tx.get_hash()] = tx
        elif isinstance(tx, PositiveGossipTransaction):
            self.gossips[tx.get_hash()] = tx
        elif isinstance(tx, PaymentTransaction):
            self.payments[tx.get_hash()] = tx
        else:
            assert False, "Can't add. Transaction type is unknown or should not be added to mempool"

    # remove all occurences of given transaction
    def remove_transaction(self, tx):
        if isinstance(tx, PrivateKeyTransaction) or \
                isinstance(tx, PenaltyTransaction) or \
                isinstance(tx, PenaltyGossipTransaction):  # should only be as part of the block
            pass
        else:
            container = None
            if isinstance(tx, PublicKeyTransaction):
                container = self.public_keys
            elif isinstance(tx, StakeHoldTransaction) or isinstance(tx, StakeReleaseTransaction):
                container = self.stake_operations
            elif isinstance(tx, CommitRandomTransaction):
                container = self.commits
            elif isinstance(tx, RevealRandomTransaction):
                container = self.reveals
            elif isinstance(tx, SplitRandomTransaction):
                container = self.shares

            elif isinstance(tx, NegativeGossipTransaction) or isinstance(tx, PositiveGossipTransaction):
                container = self.gossips
            elif isinstance(tx, PaymentTransaction):
                container = self.payments
            
            if container != None:
                tx_hash = tx.get_hash()
                if tx_hash in self.payments:
                    del container[tx_hash]
            else:
                assert False, "Can't remove. Transaction type is unknown"

    def remove_transactions(self, transactions):
        for tx in transactions:
            self.remove_transaction(tx)

    # -------------------------------------------------------------------------------
    # System tx
    # -------------------------------------------------------------------------------
    def get_transactions_for_round(self, round_type):
        if round_type == Round.PRIVATE or \
           round_type == Round.FINAL:
            return []
        elif round_type == Round.PUBLIC:
            public_keys = list(self.public_keys.values())
            self.public_keys.clear()
            return public_keys
        elif round_type == Round.COMMIT:
            commits = list(self.commits.values())
            self.commits.clear()
            return commits
        elif round_type == Round.REVEAL:
            reveals = list(self.reveals.values())
            self.reveals.clear()
            return reveals
        elif round_type == Round.SECRETSHARE:
            shares = list(self.shares.values())
            self.shares.clear()
            return shares
        else:
            assert False, "No known transactions for round"

    def pop_round_system_transactions(self, round):
        txs = self.get_transactions_for_round(round)
        return txs

    def remove_all_systemic_transactions(self):
        self.public_keys.clear()
        self.shares.clear()
        self.stake_operations.clear()
        self.commits.clear()
        self.reveals.clear()
        # don't remove payments here

    def pop_payment_transactions(self):
        payments = list(self.payments.values())
        self.payments.clear()
        return payments

    # -------------------------------------------------------------------------------
    # Gossip tx
    # -------------------------------------------------------------------------------
    def get_gossips_by_type(self, tx_type):
        """
            Method return all gossips in current mempool by gossip tx type (negative/positive/penalty)
            :param tx_type: gossip tx_type for filtering gossip list
            :return: typed gossip list
        """
        result = []
        for gossip in self.gossips.values():
            if isinstance(tx_type, NegativeGossipTransaction):
                if isinstance(gossip, NegativeGossipTransaction):
                    result.append(gossip)
                    continue
            elif isinstance(tx_type, PositiveGossipTransaction):
                if isinstance(gossip, PositiveGossipTransaction):
                    result.append(gossip)
                    continue
            elif isinstance(tx_type, PenaltyGossipTransaction):
                if isinstance(gossip, PenaltyGossipTransaction):
                    result.append(gossip)
                    continue
        return result

    def get_all_negative_gossips(self):
        """
            Method for get all negatives
            :return: all currnt negatives from mempool
        """
        return self.get_gossips_by_type(NegativeGossipTransaction())

    def get_negative_gossips_by_block(self, block_number):
        """
            Method return all gossips in current mempool by gossip tx type negative for block_number
            :param block_number: gossip tx_type for filtering gossip list
            :return: typed gossip list by block number
        """
        result = []
        typed_gossips = self.get_gossips_by_type(NegativeGossipTransaction())
        for gossip in typed_gossips:
            if gossip.number_of_block == block_number:
                result.append(gossip)
        return result

    def get_positive_gossips_by_block_hash(self, block_hash):
        """
            Method return all gossips in current mempool by gossip tx type positive by block hash
            :param block_number: gossip tx_type for filtering gossip list
            :return: typed gossip list by block number
        """
        result = []
        typed_gossips = self.get_gossips_by_type(PositiveGossipTransaction())
        for gossip in typed_gossips:
            if gossip.block_hash == block_hash:
                result.append(gossip)
        return result

    def get_penalty_gossips_by_block(self, block_number):
        """
            Method return all gossips in current mempool by gossip tx type penalty for block_number
            :param block_number: gossip tx_type for filtering gossip list
            :return: typed gossip list by block number
        """
        result = []
        typed_gossips = self.get_gossips_by_type(PenaltyGossipTransaction())
        for gossip in typed_gossips:
            if gossip.number_of_block == block_number:
                result.append(gossip)
        return result

    def append_gossip_tx(self, tx):
        """
            Add gossip transaction to mempool if it not exist
            :param tx: gossip transaction for adding to mempool
            :return: current mempool gossip list
        """
        tx_hash = tx.get_hash()
        if tx_hash not in self.gossips:
            self.gossips[tx_hash] = tx
        return self.gossips

    def pop_current_gossips(self):
        """
            Return gossips list with delete
            :return: current gossips list
        """
        result = list(self.gossips.values())
        self.gossips.clear()
        return result
