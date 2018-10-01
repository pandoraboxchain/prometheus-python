from chain.params import Round
from transaction.secret_sharing_transactions import PrivateKeyTransaction
from crypto.keys import Keys

class InvalidBlockException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

class BlockVerifier:
    def __init__(self, epoch, logger):
        self.epoch = epoch
        self.logger = logger

    def check_if_valid(self, block):

        try:

            self.validate_private_transactions_in_block(block)

        except InvalidBlockException as e:
            self.logger.error(e)
            return False

        return True

    def validate_private_transactions_in_block(self, block):

        private_key_transactions = []
        for tx in block.system_txs:
            if isinstance(tx, PrivateKeyTransaction):
                private_key_transactions.append(tx)

        current_round = self.epoch.get_current_round()

        if current_round != Round.PRIVATE:
            if len(private_key_transactions) > 0:
                raise InvalidBlockException("PrivateKeyTransaction was found in round " + current_round.name)

            return

        if len(private_key_transactions) == 0:
            raise InvalidBlockException("Block has no PrivateKeyTransaction in private round!")

        elif len(private_key_transactions) > 1:
            raise InvalidBlockException("Block has more than one PrivateKeyTransaction!")

        private_key = private_key_transactions[0].key
        expected_public = Keys.from_bytes(private_key).publickey()
        epoch_hashes = self.epoch.get_epoch_hashes()
        
        for top, _epoch_hash in epoch_hashes.items():
            public_keys = self.epoch.get_public_keys_for_epoch(top)
            if not Keys.to_bytes(expected_public) in public_keys.values():
                raise InvalidBlockException("No correspondig public key was found for private key in PrivateKeyTransaction!")