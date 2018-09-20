from Crypto.Hash import SHA256
from serialization.serializer import Serializer, Deserializer


class PaymentTransaction:
    def __init__(self):
        self.from_tx = None  # transaction hash
        self.amount = None
        self.to = None  # public key hash
        self.pubkey = None
        self.signature = None
        self.len = None

    def get_hash(self):
        # TODO find out if it is safe to use unsigned here
        return SHA256.new(self.pack_unsigned()).digest()

    def parse(self, raw_data):
        deserializer = Deserializer(raw_data)
        self.from_tx = deserializer.parse_hash()
        self.amount = deserializer.parse_u32()
        self.to = deserializer.parse_hash()
        self.pubkey = deserializer.parse_pubkey()
        self.signature = deserializer.parse_signature()
        self.len = deserializer.len
    
    def pack(self):
        raw = self.pack_unsigned()
        raw += Serializer.write_signature(self.signature)
        return raw
    
    def pack_unsigned(self):
        raw = self.from_tx
        raw += Serializer.write_u32(self.amount)
        raw += self.to 
        raw += self.pubkey
        return raw

    def get_len(self):
        return self.len
