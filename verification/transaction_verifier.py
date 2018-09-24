from transaction.secret_sharing_transactions import PrivateKeyTransaction,  PublicKeyTransaction, SplitRandomTransaction
from transaction.stake_transaction import PenaltyTransaction

from crypto.keys import Keys
from chain.params import Round

class InvalidTransactionException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

class TransactionVerifier():
    def __init__(self, epoch, permissions, epoch_block_number):
        self.epoch = epoch
        self.permissions = permissions
        self.epoch_block_number = epoch_block_number

    def check_if_valid(self, transaction):

        try:

            self.is_not_private_key_transaction(transaction)
            self.is_not_penalty_transaction(transaction)
            
            self.validate_if_public_key_transaction(transaction)
            
            self.is_sender_valid_for_current_round(transaction)
            self.is_signature_valid_for_at_least_one_epoch(transaction)

            self.validate_if_secret_sharing_transaction(transaction)
        except InvalidTransactionException as e:
            print(e)
            return False

        return True


    def is_not_private_key_transaction(self, transaction):
        if isinstance(transaction, PrivateKeyTransaction): #do not accept to mempool, because its block only tx
            raise InvalidTransactionException("Privte key transation is not allowed! Private key should be transmitted as part of a block!")

    def is_not_penalty_transaction(self, transaction):
        if isinstance(transaction, PenaltyTransaction): #do not accept to mempool, because its block only tx
            raise InvalidTransactionException("Penalty transation is not allowed! Private key should be transmitted as part of a block!")


    def is_sender_valid_for_current_round(self, transaction):
        current_round = self.epoch.get_current_round()
        epoch_hashes = self.epoch.get_epoch_hashes()
        signature_valid_for_at_least_one_valid_publickey = False
        for _top, epoch_hash in epoch_hashes.items():
            validators = self.permissions.get_ordered_pubkeys_for_round(epoch_hash, current_round)
            for validator in validators:
                if TransactionVerifier.check_signature(transaction, validator.public_key, epoch_hash) == True:
                    signature_valid_for_at_least_one_valid_publickey = True
                    break

        if not signature_valid_for_at_least_one_valid_publickey:
            raise InvalidTransactionException("Transaction was not signed by a valid public key for this round!")


    def is_signature_valid_for_at_least_one_epoch(self, transaction):
        if hasattr(transaction, "pubkey"):
            public_key = Keys.from_bytes(transaction.pubkey)
            signature_valid_for_at_least_one_epoch = False
            epoch_hashes = self.epoch.get_epoch_hashes()
            for _top, epoch_hash in epoch_hashes.items():
                valid_for_epoch = self.check_signature(transaction, public_key, epoch_hash)
                if valid_for_epoch:
                    signature_valid_for_at_least_one_epoch = True
                    break

            if not signature_valid_for_at_least_one_epoch:
                raise InvalidTransactionException("Signature is not valid for any ")

    
    def validate_if_public_key_transaction(self, transaction):
        if isinstance(transaction, PublicKeyTransaction):
            epoch_hashes = self.epoch.get_epoch_hashes()
            for _top, epoch_hash in epoch_hashes.items():
                pubkey_publishers = self.permissions.get_ordered_pubkeys_for_round(epoch_hash, Round.PRIVATE)
                allowed_pubkey = False
                for pubkey_publisher in pubkey_publishers:
                    if pubkey_publisher.public_key == Keys.from_bytes(transaction.pubkey):
                        allowed_pubkey = True
                
                if allowed_pubkey == False:
                    raise InvalidTransactionException("No valid public key found for this transaction!")
    
    def validate_if_secret_sharing_transaction(self, transaction):
        if isinstance(transaction, SplitRandomTransaction):
            self.has_enough_pieces_for_secret_sharing(transaction)

    def has_enough_pieces_for_secret_sharing(self, transaction):
        pass

    @staticmethod
    def check_signature(tx, pubkey, epoch_hash):
        tx_hash = None
        if hasattr(tx, 'get_signing_hash') and callable(getattr(tx, 'get_signing_hash')):
            tx_hash = tx.get_signing_hash(epoch_hash)
        else:
            tx_hash = tx.get_hash()
        
        return pubkey.verify(tx_hash, (tx.signature,))