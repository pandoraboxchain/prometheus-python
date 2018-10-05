from verification.acceptor import Acceptor, AcceptionException

from chain.params import Round

from transaction.secret_sharing_transactions import PrivateKeyTransaction
from crypto.keys import Keys
from crypto.private import Private


class BlockAcceptor(Acceptor):

    def __init__(self, epoch, logger):
        super().__init__(logger)
        self.epoch = epoch

    def validate(self, block):

        current_round = self.epoch.get_current_round()
        current_block_number = self.epoch.get_current_timeframe_block_number()

        self.validate_timeslot(block, current_block_number)
        self.validate_private_transactions_in_block(block, current_round)

    def validate_timeslot(self, block, current_block_number):

        for prev_hash in block.prev_hashes:
            prev_hash_number = self.epoch.dag.get_block_number(prev_hash)
            if prev_hash_number >= current_block_number:
                raise AcceptionException("Block refers to blocks in current or future timeslots!")

    def validate_private_transactions_in_block(self, block, current_round):

        private_key_transactions = []
        for tx in block.system_txs:
            if isinstance(tx, PrivateKeyTransaction):
                private_key_transactions.append(tx)

        private_key_transactions_count_in_block = len(private_key_transactions)

        if current_round != Round.PRIVATE:
            if private_key_transactions_count_in_block > 0:
                raise AcceptionException("PrivateKeyTransaction was found in round " + current_round.name)

            return

        if private_key_transactions_count_in_block == 0:
            raise AcceptionException("Block has no PrivateKeyTransaction in private round!")

        elif private_key_transactions_count_in_block > 1:
            raise AcceptionException("Block has more than one PrivateKeyTransaction!")

        private_key = private_key_transactions[0].key
        expected_public = Private.publickey(private_key)
        epoch_hashes = self.epoch.get_epoch_hashes()

        for top, _epoch_hash in epoch_hashes.items():
            public_keys = self.epoch.get_public_keys_for_epoch(top)
            if not Keys.to_bytes(expected_public) in public_keys.values():
                raise AcceptionException(
                    "No correspondig public key was found for private key in PrivateKeyTransaction!")