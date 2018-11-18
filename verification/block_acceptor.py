from verification.acceptor import Acceptor, AcceptionException

from chain.params import Round

from transaction.secret_sharing_transactions import PrivateKeyTransaction
from crypto.keys import Keys
from crypto.private import Private


#TODO check if block don't have itself in prev_hashes

class BlockAcceptor(Acceptor):

    def __init__(self, epoch, logger):
        super().__init__(logger)
        self.epoch = epoch

    def validate(self, block):

        current_round = self.epoch.get_current_round()
        current_block_number = self.epoch.get_current_timeframe_block_number()
        prev_hashes = block.prev_hashes

        self.validate_timeslot(block, current_block_number)
        self.validate_non_ancestor_prev_hashes(prev_hashes) #turn off for out of timeslot case
        self.validate_longest_chain_goes_first(prev_hashes)
        self.validate_private_transactions_in_block(block, current_round)

    # no previous hash should be ancestor of another previous hash 
    def validate_non_ancestor_prev_hashes(self, prev_hashes):
        for prev_hash1 in prev_hashes:
            for prev_hash2 in prev_hashes:
                if prev_hash1 != prev_hash2:
                    if  self.epoch.dag.is_ancestor(prev_hash1, prev_hash2) or \
                        self.epoch.dag.is_ancestor(prev_hash2, prev_hash1):
                            raise AcceptionException("Block previous hashes are self referential")

    def validate_timeslot(self, block, current_block_number):
        for prev_hash in block.prev_hashes:
            prev_hash_number = self.epoch.dag.get_block_number(prev_hash)
            if prev_hash_number >= current_block_number:
                raise AcceptionException("Block refers to blocks in current or future timeslots")

    def validate_longest_chain_goes_first(self, prev_hashes):
        dag = self.epoch.dag
        common_ancestor = dag.get_common_ancestor(prev_hashes)
        lengths = [dag.calculate_chain_length(prev_hash, common_ancestor) for prev_hash in prev_hashes]
        max_length = max(lengths)
        first_chain_length = dag.calculate_chain_length(prev_hashes[0], common_ancestor)
        if first_chain_length != max_length:
            raise AcceptionException("Block first ancestor should link to longest chain")

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


        return # this check is too slow and I'm not sure if it's needed at all
        private_key = private_key_transactions[0].key
        expected_public = Private.publickey(private_key)
        epoch_hashes = self.epoch.get_epoch_hashes()

        for top, _epoch_hash in epoch_hashes.items():
            public_keys = self.epoch.get_public_keys_for_epoch(top)
            if not Keys.to_bytes(expected_public) in public_keys.values():
                raise AcceptionException(
                    "No corresponding public key was found for private key in PrivateKeyTransaction!")