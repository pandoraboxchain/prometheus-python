from tools.time import Time
from crypto.keys import Keys
from crypto.private import Private
from transaction.payment_transaction import PaymentTransaction
from transaction.commit_transactions import CommitRandomTransaction, \
                                            RevealRandomTransaction
from transaction.gossip_transaction import NegativeGossipTransaction, \
                                           PositiveGossipTransaction, \
                                           PenaltyGossipTransaction
from transaction.secret_sharing_transactions import PublicKeyTransaction, \
                                                    PrivateKeyTransaction, \
                                                    SplitRandomTransaction
from transaction.stake_transaction import StakeHoldTransaction, \
                                          StakeReleaseTransaction, \
                                          PenaltyTransaction

from transaction.utxo import Utxo, COINBASE_IDENTIFIER
from chain.params import BLOCK_REWARD

class TransactionFactory:

    @staticmethod
    def create_payment_transaction(from_tx,  amount, to, node_private):
        tx = PaymentTransaction()
        tx.from_tx = from_tx
        tx.amount = amount
        tx.to = to
        tx.pubkey = Private.publickey(node_private)
        tx.signature = Private.sign(tx.get_hash(), node_private)
        return tx

    @staticmethod
    def create_negative_gossip_transaction(number_of_block, node_private):
        tx = NegativeGossipTransaction()
        tx.timestamp = Time.get_current_time()
        tx.number_of_block = number_of_block
        tx.pubkey = Private.publickey(node_private)
        tx.signature = Private.sign(tx.get_hash(), node_private)
        return tx

    @staticmethod
    def create_positive_gossip_transaction(block_hash, node_private):
        tx = PositiveGossipTransaction()
        tx.timestamp = Time.get_current_time()
        tx.block_hash = block_hash
        tx.pubkey = Private.publickey(node_private)
        tx.signature = Private.sign(tx.get_hash(), node_private)
        return tx

    @staticmethod
    def create_penalty_gossip_transaction(conflict, node_private):
        tx = PenaltyGossipTransaction()
        tx.timestamp = Time.get_current_time()
        tx.conflicts = conflict
        tx.signature = Private.sign(tx.get_hash(), node_private)
        return tx

    @staticmethod
    def create_commit_reveal_pair(node_private, random_bytes, pubkey_index, epoch_hash):
        private = Private.generate()
        encoded = Private.encrypt(random_bytes, private)

        commit = TransactionFactory.create_commit_random_transaction(encoded, pubkey_index, epoch_hash, node_private)
        reveal = TransactionFactory.create_reveal_random_transaction(commit.get_hash(), private)

        return commit, reveal

    @staticmethod
    def create_commit_random_transaction(rand, pubkey_index, epoch_hash, node_private):
        tx = CommitRandomTransaction()
        tx.rand = rand
        tx.pubkey_index = pubkey_index
        tx.signature = Private.sign(tx.get_signing_hash(epoch_hash), node_private)
        return tx

    @staticmethod
    def create_reveal_random_transaction(commit_hash, private):
        tx = RevealRandomTransaction()
        tx.commit_hash = commit_hash
        tx.key = Keys.to_bytes(private)
        return tx

    @staticmethod
    def create_public_key_transaction(generated_private, epoch_hash, validator_index, node_private):
        tx = PublicKeyTransaction()
        tx.generated_pubkey = Private.publickey(generated_private)
        tx.pubkey_index = validator_index
        tx.signature = Private.sign(tx.get_signing_hash(epoch_hash), node_private)
        return tx

    @staticmethod
    def create_private_key_transaction(epoch_private_key):
        tx = PrivateKeyTransaction()
        tx.key = Keys.to_bytes(epoch_private_key)
        return tx

    @staticmethod
    def create_split_random_transaction(encoded_splits, pubkey_index, epoch_hash, node_private):
        tx = SplitRandomTransaction()
        tx.pieces = encoded_splits
        tx.pubkey_index = pubkey_index
        tx.signature = Private.sign(tx.get_signing_hash(epoch_hash), node_private)
        return tx

    @staticmethod
    def create_stake_hold_transaction(amount, node_private):
        tx = StakeHoldTransaction()
        tx.amount = amount
        tx.pubkey = Private.publickey(node_private)
        tx.signature = Private.sign(tx.get_hash(), node_private)
        return tx

    @staticmethod
    def create_stake_release_transaction(node_private):
        tx = StakeReleaseTransaction()
        tx.pubkey = Private.publickey(node_private)
        tx.signature = Private.sign(tx.get_hash(), node_private)
        return tx

    @staticmethod
    def create_penalty_transaction(conflicts, node_private):
        tx = PenaltyTransaction()
        tx.conflicts = conflicts
        tx.signature = Private.sign(tx.get_hash(), node_private)
        return tx

    @staticmethod
    def create_block_reward(address, block_number):
        #block number is random data provider against hash collisions
        return TransactionFactory.create_payment(COINBASE_IDENTIFIER, block_number, [address], [BLOCK_REWARD])

    @staticmethod
    def create_payment(input, number, outputs, amounts):
        tx = PaymentTransaction()
        tx.input = input
        tx.number = number
        tx.outputs = outputs
        tx.amounts = amounts
        return tx



