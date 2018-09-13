from transaction.commit_transactions import CommitRandomTransaction, RevealRandomTransaction
from transaction.stake_transaction import StakeHoldTransaction, PenaltyTransaction, StakeReleaseTransaction
from transaction.secret_sharing_transactions import PublicKeyTransaction, PrivateKeyTransaction, SplitRandomTransaction

from serialization.serializer import Serializer, Deserializer


class Type():
    PUBLIC = 0
    RANDOM = 1
    PRIVATE = 2
    COMMIT = 3
    REVEAL = 4
    STAKEHOLD = 5
    STAKERELEASE = 6
    PENALTY = 7

class TransactionParser():
    def parse(raw_data):
        deserializer = Deserializer(raw_data)
        tx_type = deserializer.parse_u8()
        if tx_type == Type.PUBLIC:
            tx = PublicKeyTransaction()
        elif tx_type == Type.RANDOM:
            tx = SplitRandomTransaction()
        elif tx_type == Type.PRIVATE:
            tx = PrivateKeyTransaction()
        elif tx_type == Type.COMMIT:
            tx = CommitRandomTransaction()
        elif tx_type == Type.REVEAL:
            tx = RevealRandomTransaction()

        elif tx_type == Type.STAKEHOLD:
            tx = StakeHoldTransaction()
        elif tx_type == Type.STAKERELEASE:
            tx = StakeReleaseTransaction()
        elif tx_type == Type.PENALTY:
            tx = PenaltyTransaction()
        else:
            assert False, "Cannot parse unknown transaction type"
        tx.parse(deserializer.data)
        return tx

    def pack(tx):
        raw = b''
        if isinstance(tx, PublicKeyTransaction):
            raw += Serializer.write_u8(Type.PUBLIC)
        elif isinstance(tx, SplitRandomTransaction):
            raw += Serializer.write_u8(Type.RANDOM)
        elif isinstance(tx, PrivateKeyTransaction):
            raw += Serializer.write_u8(Type.PRIVATE)

        elif isinstance(tx, CommitRandomTransaction):
            raw += Serializer.write_u8(Type.COMMIT)
        elif isinstance(tx, RevealRandomTransaction):
            raw += Serializer.write_u8(Type.REVEAL)

        elif isinstance(tx, StakeHoldTransaction):
            raw += Serializer.write_u8(Type.STAKEHOLD)
        elif isinstance(tx, StakeReleaseTransaction):
            raw += Serializer.write_u8(Type.STAKERELEASE)
        elif isinstance(tx, PenaltyTransaction):
            raw += Serializer.write_u8(Type.PENALTY)
        else:
            assert False, "Cannot pack unknown transaction type"
        raw += tx.pack()
        return raw


