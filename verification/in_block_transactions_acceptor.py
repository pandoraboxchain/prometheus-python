from verification.acceptor import Acceptor, AcceptionException

from transaction.secret_sharing_transactions import PublicKeyTransaction
from transaction.commit_transactions import RevealRandomTransaction

from chain.params import Round

from crypto.keys import Keys


class InBlockTransactionsAcceptor(Acceptor):

    def __init__(self, epoch, permissions, logger):
        super().__init__(logger)
        self.epoch = epoch
        self.permissions = permissions

    def validate(self, transaction):
        self.is_signature_valid_for_at_least_one_epoch(transaction)
        self.is_sender_valid_for_current_round(transaction)

    def is_signature_valid_for_at_least_one_epoch(self, transaction):
        if hasattr(transaction, "pubkey"):
            public_key = Keys.from_bytes(transaction.pubkey)
            signature_valid_for_at_least_one_epoch = False
            epoch_hashes = self.epoch.get_epoch_hashes()
            for _top, epoch_hash in epoch_hashes.items():
                if Acceptor.check_transaction_signature(transaction, public_key, epoch_hash):
                    signature_valid_for_at_least_one_epoch = True
                    break

            if not signature_valid_for_at_least_one_epoch:
                raise AcceptionException("Signature is not valid for any epoch!")

    def is_sender_valid_for_current_round(self, transaction):

        if not Acceptor.is_randomizer_transaction(transaction):
            return

        current_round = self.epoch.get_current_round()
        epoch_hashes = self.epoch.get_epoch_hashes()
        signature_valid_for_at_least_one_valid_publickey = False
        for _top, epoch_hash in epoch_hashes.items():

            # corresponding commit transaction key was already checked in
            # MempoolTransactionsAcceptor.has_corresponding_commit_transaction
            if isinstance(transaction, RevealRandomTransaction) and current_round == Round.REVEAL:
                signature_valid_for_at_least_one_valid_publickey = True
                break

            validators = self.permissions.get_ordered_randomizers_pubkeys_for_round(epoch_hash, current_round)

            # if has index, use index to
            if hasattr(transaction, 'pubkey_index'):
                if len(validators) <= transaction.pubkey_index:
                    raise AcceptionException("Public key index out of bounds!")

                validator = validators[transaction.pubkey_index]
                if Acceptor.check_transaction_signature(transaction, validator.public_key, epoch_hash):
                    signature_valid_for_at_least_one_valid_publickey = True
                    break

        if not signature_valid_for_at_least_one_valid_publickey:
            raise AcceptionException("Transaction was not signed by a valid public key for this round!")