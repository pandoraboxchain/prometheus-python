from result import Ok, Err
from verification.acceptor import Acceptor, AcceptionException

from chain.params import Round

from transaction.secret_sharing_transactions import PrivateKeyTransaction
from crypto.keys import Keys
from crypto.private import Private


#TODO check if block don't have itself in prev_hashes

# interface, probably should go to separate file
class Verifier:
    def verify(self):
        raise NotImplementedError("verify() method should be implemented in a child class!")

class TimeslotVerifier(Verifier):
    def __init__(self, block, current_block_number, epoch):
        self.block = block
        self.current_block_number = current_block_number
        self.epoch = epoch
    
    def verify(self):
        for prev_hash in self.block.prev_hashes:
            prev_hash_number = self.epoch.dag.get_block_number(prev_hash)
            if prev_hash_number >= self.current_block_number:
                    raise AcceptionException("Block refers to blocks in current or future timeslots!")
            
class PrivateKeyInBlockVerifier(Verifier):
    def __init__(self, block, current_round, epoch):
        self.block = block
        self.current_round = current_round
        self.epoch = epoch

    def verify(self):
        private_key_transactions = []
        for tx in self.block.system_txs:
            if isinstance(tx, PrivateKeyTransaction):
                private_key_transactions.append(tx)

        private_key_transactions_count_in_block = len(private_key_transactions)

        if self.current_round != Round.PRIVATE:
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


class BlockVerifier(Verifier):
    def __init__(self, epoch, block, timeslot_number):
        self.epoch = epoch
        self.block = block
        self.timeslot_number = timeslot_number
        current_round = self.epoch.get_current_round()
        timeslot_verifier = TimeslotVerifier(block, timeslot_number, epoch)
        private_tx_in_block_verifier = PrivateKeyInBlockVerifier(block, current_round, epoch)

        self.verifiers = [timeslot_verifier, private_tx_in_block_verifier]
    
    def verify(self):
        try:
            for verifier in self.verifiers:
                verifier.verify()
        except AcceptionException as e:
            return Err(e)

        return Ok(True)
        