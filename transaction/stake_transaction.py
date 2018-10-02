from hashlib import sha256
from serialization.serializer import Serializer, Deserializer


class StakeHoldTransaction:

    def __init__(self):
        self.amount = None
        self.pubkey = None
        self.signature = None
        self.len = None

    def get_hash(self):
        return sha256(Serializer.write_u16(self.amount) + self.pubkey).digest()

    def parse(self, raw_data):
        deserializer = Deserializer(raw_data)    
        self.amount = deserializer.parse_u16()
        self.pubkey = deserializer.parse_pubkey()
        self.signature = deserializer.parse_signature()
        self.len = deserializer.len
    
    def pack(self):
        raw = Serializer.write_u16(self.amount)
        raw += self.pubkey
        raw += Serializer.write_signature(self.signature)
        return raw

    def get_len(self):
        return self.len


class PenaltyTransaction:

    def __init__(self):
        self.conflicts = []
        self.signature = None
        self.len = None

    def parse(self, raw_data):
        deserializer = Deserializer(raw_data)
        conflict_count = deserializer.parse_u8()
        self.conflicts = []
        for _ in range(0, conflict_count):
            conflict = deserializer.parse_hash()
            self.conflicts.append(conflict)
        self.signature = deserializer.parse_signature()
        self.len = deserializer.len
    
    def pack(self):
        raw = self.pack_conflicts()
        raw += Serializer.write_signature(self.signature)      
        return raw

    def pack_conflicts(self):
        raw = Serializer.write_u8(len(self.conflicts))
        for conflict in self.conflicts:
            raw += conflict
        return raw
    
    def get_len(self):
        return self.len

    def get_hash(self):
        return sha256(self.pack_conflicts()).digest()


class StakeReleaseTransaction:

    def __init__(self):
        self.pubkey = None
        self.signature = None
        self.len = None

    def get_hash(self):
        return sha256(self.pubkey).digest()

    def parse(self, raw_data):
        deserializer = Deserializer(raw_data)
        self.pubkey = deserializer.parse_pubkey()
        self.signature = deserializer.parse_signature()
        self.len = deserializer.len
    
    def pack(self):
        raw = self.pubkey
        raw += Serializer.write_signature(self.signature)
        return raw

    def get_len(self):
        return self.len
