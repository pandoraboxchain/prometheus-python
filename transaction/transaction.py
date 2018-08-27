import struct
from Crypto.Hash import SHA256
from transaction.stake_transaction import StakeHoldTransaction, PenaltyTransaction, StakeReleaseTransaction
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
        tx_type = struct.unpack_from("B", raw_data)[0]
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
        tx.parse(raw_data[1:])
        return tx

    def pack(tx):
        raw = b''
        if isinstance(tx, PublicKeyTransaction):
            raw += struct.pack("B", Type.PUBLIC)
        elif isinstance(tx, SplitRandomTransaction):
            raw += struct.pack("B", Type.RANDOM)
        elif isinstance(tx, PrivateKeyTransaction):
            raw += struct.pack("B", Type.PRIVATE)

        elif isinstance(tx, CommitRandomTransaction):
            raw += struct.pack("B", Type.COMMIT)
        elif isinstance(tx, RevealRandomTransaction):
            raw += struct.pack("B", Type.REVEAL)

        elif isinstance(tx, StakeHoldTransaction):
            raw += struct.pack("B", Type.STAKEHOLD)
        elif isinstance(tx, StakeReleaseTransaction):
            raw += struct.pack("B", Type.STAKERELEASE)
        elif isinstance(tx, PenaltyTransaction):
            raw += struct.pack("B", Type.PENALTY)
        else:
            assert False, "Cannot pack unknown transaction type"
        raw += tx.pack()
        return raw

class CommitRandomTransaction():
    def parse(self, raw_data):
        deserializer = Deserializer(raw_data)
        self.rand = deserializer.parse_encrypted_data()
        self.pubkey = deserializer.parse_pubkey()
        self.signature = deserializer.parse_signature()
        self.len = deserializer.get_len()
    
    def pack(self):
        return  Serializer.write_encrypted_data(self.rand) + \
                self.pubkey + \
                Serializer.write_signature(self.signature)
    
    def get_len(self):
        return self.len

    #this hash includes epoch_hash for checking if random wasn't reused
    def get_signing_hash(self, epoch_hash):
        return SHA256.new(self.rand + self.pubkey + epoch_hash).digest()
    
    #this hash is for linking this transaction from reveal
    def get_reference_hash(self):
        return SHA256.new(self.pack()).digest()

class RevealRandomTransaction():
    def parse(self, raw_data):
        deserializer = Deserializer(raw_data)
        self.commit_hash = deserializer.parse_hash()
        self.key = deserializer.parse_private_key()
        self.len = deserializer.get_len()
    
    def pack(self):
        raw = self.commit_hash
        raw += Serializer.write_private_key(self.key)
        return raw
    
    def get_len(self):
        return self.len

    def get_hash(self):
        return SHA256.new(self.pack()).digest()

class PublicKeyTransaction():
    def get_hash(self):
        return SHA256.new(self.generated_pubkey + self.sender_pubkey).digest()

    def parse(self, raw_data):
        self.generated_pubkey = raw_data[:216]
        self.sender_pubkey = raw_data[216:432]
        self.signature = int.from_bytes(raw_data[432:560], byteorder='big')
    
    def pack(self):
        return self.generated_pubkey + self.sender_pubkey + self.signature.to_bytes(128, byteorder='big')
    
    def get_len(self):
        return 560

class PrivateKeyTransaction():
    def parse(self, raw_data):
        key_length = struct.unpack_from("H", raw_data)[0]
        self.len = 2 + key_length
        self.key = raw_data[2:self.len]
    
    def pack(self):
        raw = struct.pack("H", len(self.key))
        raw += self.key
        return raw
    
    def get_len(self):
        return self.len

    def get_hash(self):
        return SHA256.new(self.pack()).digest()

class SplitRandomTransaction():
    def parse(self, raw_data):
        self.signature = int.from_bytes(raw_data[0:128], byteorder='big')
        self.pieces = []
        pieces_len = struct.unpack_from("H", raw_data, 128)[0]
        pieces_bytes = raw_data[130:]
        self.len = 130
        for i in range(0, pieces_len):
            piece_size = struct.unpack_from("B", pieces_bytes)[0]
            piece = pieces_bytes[1:piece_size + 1]
            self.pieces.append(piece)
            pieces_bytes = pieces_bytes[1 + piece_size:]
            self.len += 1 + piece_size
            
    def pack(self):
        raw = self.signature.to_bytes(128, byteorder='big')
        raw += self.pack_pieces()
        return raw
    
    def pack_pieces(self):
        raw = struct.pack("H", len(self.pieces))
        for piece in self.pieces:
            piece_len = len(piece)
            raw += struct.pack("B", len(piece))
            raw += piece
        return raw
    
    def get_len(self):
        return self.len

    def get_hash(self):
        return SHA256.new(self.pack_pieces()).digest()


