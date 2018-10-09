from serialization.serializer import Serializer, Deserializer
from hashlib import sha256

class CommitRandomTransaction:

    def __init__(self):
        self.rand = None
        self.pubkey_index = None
        self.signature = None
        self.len = None

    def parse(self, raw_data):
        deserializer = Deserializer(raw_data)
        self.rand = deserializer.parse_encrypted_data()
        self.pubkey_index = deserializer.parse_u32()
        self.signature = deserializer.parse_signature()
        self.len = deserializer.get_len()
    
    def pack(self):
        return Serializer.write_encrypted_data(self.rand) + \
               Serializer.write_u32(self.pubkey_index) + \
               Serializer.write_signature(self.signature)
    
    def get_len(self):
        return self.len

    # this hash includes epoch_hash for checking if random wasn't reused
    def get_signing_hash(self, epoch_hash):
        return sha256(self.rand + self.pubkey_index.to_bytes(4, byteorder='big') + epoch_hash).digest()
    
    # this hash is for linking this transaction from reveal
    def get_hash(self):
        return sha256(self.pack()).digest()


class RevealRandomTransaction:

    def __init__(self):
        self.commit_hash = None
        self.key = None
        self.len = None

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
        return sha256(self.pack()).digest()
