import struct
from Crypto.Hash import SHA256
from transaction.transaction import PrivateKeyTransaction, PenaltyTransaction, PublicKeyTransaction
from crypto.keys import Keys
from chain.epoch import Epoch

class TransactionVerifier():
    def __init__(self, epoch, permissions, epoch_block_number):
        self.epoch = epoch
        self.permissions = permissions
        self.epoch_block_number = epoch_block_number

    def check_if_valid(self, transaction):
        if isinstance(transaction, PrivateKeyTransaction): #do not accept to mempool, because its block only tx
            return False
        elif isinstance(transaction, PenaltyTransaction): #do not accept to mempool, because its block only tx
            return False

        elif isinstance(transaction, PublicKeyTransaction):
            epoch_hashes = self.epoch.get_epoch_hashes()
            for _top, epoch_hash in epoch_hashes.items():
                pubkey_publishers = self.permissions.get_ordered_pubkeys_for_last_round(epoch_hash)
                allowed_pubkey = False
                for pubkey_publisher in pubkey_publishers:
                    if pubkey_publisher.public_key == Keys.from_bytes(transaction.pubkey):
                        allowed_pubkey = True
                
                if allowed_pubkey == False:
                    return False
        
        if hasattr(transaction, "pubkey"):
            public_key = Keys.from_bytes(transaction.pubkey)
            signature_valid_for_at_least_one_epoch = False
            epoch_hashes = self.epoch.get_epoch_hashes()
            for _top, epoch_hash in epoch_hashes.items():
                valid_for_epoch = self.check_signature(transaction, public_key, epoch_hash)
                if valid_for_epoch:
                    signature_valid_for_at_least_one_epoch = True
                    break
            return signature_valid_for_at_least_one_epoch
        else:
            return True
    
    def check_signature(self, tx, pubkey, epoch_hash):
        tx_hash = None
        if hasattr(tx, 'get_signing_hash') and callable(getattr(tx, 'get_signing_hash')):
            tx_hash = tx.get_signing_hash(epoch_hash)
        else:
            tx_hash = tx.get_hash()
        
        return pubkey.verify(tx_hash, (tx.signature,))