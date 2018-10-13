from serialization.serializer import Serializer, Deserializer
from hashlib import sha256


class PublicKeyTransaction:
    def __init__(self):
        self.generated_pubkey = None
        self.pubkey_index = None
        self.signature = None
        self.len = None

    def pack_unsigned(self):
        raw = self.generated_pubkey 
        raw += Serializer.write_u32(self.pubkey_index)
        return raw

    def get_hash(self):
        assert self.signature, "This method is for referencing. Use get_signing_hash if you have to sign a transaction"
        return sha256(self.pack()).digest()
    
    def get_signing_hash(self, epoch_hash):
        return sha256(self.pack_unsigned() + epoch_hash).digest()

    def parse(self, raw_data):
        deserializer = Deserializer(raw_data)
        self.generated_pubkey = deserializer.parse_pubkey()
        self.pubkey_index = deserializer.parse_u32()
        self.signature = deserializer.parse_signature()
        self.len = deserializer.get_len()
    
    def pack(self):
        return self.generated_pubkey + Serializer.write_u32(self.pubkey_index) + Serializer.write_signature(self.signature)
    
    def get_len(self):
        return self.len


class PrivateKeyTransaction:

    def __init__(self):
        self.key = None
        self.len = None

    def parse(self, raw_data):
        deserializer = Deserializer(raw_data)
        self.key = deserializer.parse_private_key()
        self.len = deserializer.get_len()
    
    def pack(self):
        raw = Serializer.write_private_key(self.key)
        return raw
    
    def get_len(self):
        return self.len

    def get_hash(self):
        return sha256(self.pack()).digest()


class SplitRandomTransaction:

    def __init__(self):
        self.signature = None
        self.pubkey_index = None
        self.pieces = []
        self.len = None

    def parse(self, raw_data):
        deserializer = Deserializer(raw_data)
        self.signature = deserializer.parse_signature()
        self.pubkey_index = deserializer.parse_u32()
        self.pieces = []
        pieces_len = deserializer.parse_u16()
        for _ in range(0, pieces_len):
            piece_size = deserializer.parse_u8()
            piece = deserializer.read_and_move(piece_size)
            self.pieces.append(piece)
        self.len = deserializer.get_len()
            
    def pack(self):
        raw = Serializer.write_signature(self.signature)
        raw += Serializer.write_u32(self.pubkey_index)
        raw += self.pack_pieces()
        return raw
    
    def pack_pieces(self):
        raw = Serializer.write_u16(len(self.pieces))
        for piece in self.pieces:
            raw += Serializer.write_u8(len(piece))
            raw += piece
        return raw
    
    def get_len(self):
        return self.len

    def get_signing_hash(self, epoch_hash):
        return sha256(self.pack_pieces() + epoch_hash).digest()

    def get_hash(self):
        assert self.signature, "This method is for referencing. Use get_signing_hash if you have to sign a transaction"
        return sha256(self.pack()).digest()