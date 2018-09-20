from Crypto.Hash import SHA256
import struct


class StakeHoldTransaction:

    def __init__(self):
        self.amount = None
        self.pubkey = None
        self.signature = None

    def get_hash(self):
        raw_amount = self.amount.to_bytes(2, byteorder='big')
        return SHA256.new(raw_amount + self.pubkey).digest()

    def parse(self, raw_data):
        self.amount = struct.unpack_from("H", raw_data)[0]
        self.pubkey = raw_data[2:218]
        self.signature = int.from_bytes(raw_data[218: 218 + 128], byteorder='big')
    
    def pack(self):
        raw = struct.pack("H", self.amount)
        raw += self.pubkey
        raw += self.signature.to_bytes(128, byteorder='big')
        return raw

    @staticmethod
    def get_len():
        return 218 + 128


class PenaltyTransaction:

    def __init__(self):
        self.conflicts = []
        self.signature = None
        self.len = None

    def parse(self, raw_data):
        conflict_count = struct.unpack_from("B", raw_data)[0]
        raw_conflicts = raw_data[1:]
        self.conflicts = []
        for i in range(0, conflict_count):
            conflict = raw_conflicts[i * 32 : (i+1) * 32]
            self.conflicts.append(conflict)
        raw_signature = raw_conflicts[32 * conflict_count:]
        self.signature = int.from_bytes(raw_signature[:128], byteorder='big') #pubkey should be of block signer
        self.len = 1 + conflict_count * 32 + 128
    
    def pack(self):
        raw = self.pack_conflicts()
        raw += self.signature.to_bytes(128, byteorder='big')        
        return raw

    def pack_conflicts(self):
        raw = struct.pack("B", len(self.conflicts))
        for conflict in self.conflicts:
            raw += conflict
        return raw
    
    def get_len(self):
        return self.len

    def get_hash(self):
        return SHA256.new(self.pack_conflicts()).digest()


class StakeReleaseTransaction:

    def __init__(self):
        self.pubkey = None
        self.signature = None

    def get_hash(self):
        return SHA256.new(self.pubkey).digest()

    def parse(self, raw_data):
        self.pubkey = raw_data[0:216]
        self.signature = int.from_bytes(raw_data[216: 216 + 128], byteorder='big')
    
    def pack(self):
        raw = self.pubkey
        raw += self.signature.to_bytes(128, byteorder='big')
        return raw

    @staticmethod
    def get_len():
        return 218 + 128
