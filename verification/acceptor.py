from abc import ABCMeta, abstractmethod

from transaction.secret_sharing_transactions import PublicKeyTransaction, SplitRandomTransaction
from transaction.commit_transactions import CommitRandomTransaction, RevealRandomTransaction
from crypto.public import Public

from transaction.secret_sharing_transactions import PrivateKeyTransaction

class AcceptionException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class Acceptor:

    __metaclass__ = ABCMeta

    def __init__(self, logger):
        self.logger = logger

    def check_if_valid(self, object_to_validate):

        try:
            self.validate(object_to_validate)

        except AcceptionException as e:
            self.logger.error(e)
            return False

        return True

    @abstractmethod
    def validate(self):
        raise NotImplementedError("'validate' function should be implemented by a child class!")

    @staticmethod
    def check_transaction_signature(tx, pubkey, epoch_hash):

        if hasattr(tx, 'get_signing_hash') and callable(getattr(tx, 'get_signing_hash')):
            tx_hash = tx.get_signing_hash(epoch_hash)
        else:
            tx_hash = tx.get_hash()

        if isinstance(tx, RevealRandomTransaction):
            # TODO implement check by key accordance
            return True

        return Public.verify(tx_hash, tx.signature, pubkey)

    @staticmethod
    def is_randomizer_transaction(transaction):
        if isinstance(transaction, PublicKeyTransaction) or \
                isinstance(transaction, SplitRandomTransaction) or \
                isinstance(transaction, PrivateKeyTransaction) or \
                isinstance(transaction, CommitRandomTransaction) or \
                isinstance(transaction, RevealRandomTransaction):
            return True
        return False
