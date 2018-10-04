from verification.acceptor import Acceptor, AcceptionException

from transaction.secret_sharing_transactions import SplitRandomTransaction
from transaction.commit_transactions import RevealRandomTransaction
from transaction.stake_transaction import PenaltyTransaction
from chain.params import MINIMAL_SECRET_SHARERS

from transaction.secret_sharing_transactions import PrivateKeyTransaction


class MempoolTransactionsAcceptor(Acceptor):
    def __init__(self, epoch, permissions, logger):
        super().__init__(logger)
        self.epoch = epoch
        self.permissions = permissions

    def validate(self, transaction):
        self.is_not_private_key_transaction(transaction)
        self.is_not_penalty_transaction(transaction)

        self.is_sender_valid_for_current_round(transaction)

        self.validate_if_secret_sharing_transaction(transaction)
        self.validate_reveal_random_transaction(transaction)

    def is_not_private_key_transaction(self, transaction):
        if isinstance(transaction, PrivateKeyTransaction):  # do not accept to mempool, because its block only tx
            raise AcceptionException(
                "Private key transation is not allowed! Private key should be transmitted as part of a block!")

    def is_not_penalty_transaction(self, transaction):
        if isinstance(transaction, PenaltyTransaction):  # do not accept to mempool, because its block only tx
            raise AcceptionException(
                "Penalty transation is not allowed! Private key should be transmitted as part of a block!")

    def validate_if_secret_sharing_transaction(self, transaction):
        if isinstance(transaction, SplitRandomTransaction):
            self.has_enough_pieces_for_secret_sharing(transaction)

    def validate_reveal_random_transaction(self, transaction):
        if isinstance(transaction, RevealRandomTransaction):
            self.has_corresponding_commit_transaction(transaction)

    def has_corresponding_commit_transaction(self, transaction):
        epoch_hashes = self.epoch.get_epoch_hashes()
        commit_hash = transaction.commit_hash
        for top, _epoch_hash in epoch_hashes.items():
            commits = self.epoch.get_commits_for_epoch(top)
            if commit_hash not in commits:
                raise AcceptionException(
                    "Reveal transaction has no corresponding commit transaction in the chain!")

    def has_enough_pieces_for_secret_sharing(self, transaction):
        if len(transaction.pieces) < MINIMAL_SECRET_SHARERS:
            raise AcceptionException("SplitRandomTransaction has not enough pieces!")

    def is_sender_valid_for_current_round(self, transaction):
        if not Acceptor.is_randomizer_transaction(transaction):
            return

        current_round = self.epoch.get_current_round()
        epoch_hashes = self.epoch.get_epoch_hashes()
        signature_valid_for_at_least_one_valid_publickey = False
        for _top, epoch_hash in epoch_hashes.items():
            validators = self.permissions.get_ordered_randomizers_pubkeys_for_round(epoch_hash, current_round)
            for validator in validators:
                if Acceptor.check_transaction_signature(transaction, validator.public_key, epoch_hash):
                    signature_valid_for_at_least_one_valid_publickey = True
                    break

        if not signature_valid_for_at_least_one_valid_publickey:
            raise AcceptionException("Transaction was not signed by a valid public key for this round!")

