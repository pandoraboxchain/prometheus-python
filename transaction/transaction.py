from Crypto.Hash import SHA256
import struct

class Type():
    COMMIT = 0
    REVEAL = 1
    PARTIAL = 2

class TransactionParser():
    def parse(raw_data):
        tx_type = struct.unpack_from("B", raw_data)[0]
        if tx_type == Type.COMMIT:
            tx = CommitRandomTransaction()
        if tx_type == Type.REVEAL:
            tx = RevealRandomTransaction()
        tx.parse(raw_data[1:])
        return tx

    def pack(tx):
        raw = b''
        if isinstance(tx, CommitRandomTransaction):
            raw += struct.pack("B", Type.COMMIT)
        elif isinstance(tx, RevealRandomTransaction):
            raw += struct.pack("B", Type.REVEAL)
        raw += tx.pack()
        return raw

class CommitRandomTransaction():
    def get_hash(self):
        return SHA256.new(self.rand + self.pubkey)

    def parse(self, raw_data):
        self.rand = raw_data[:128]
        self.pubkey = raw_data[128:256]
        self.signature = raw_data[256:384]
    
    def pack(self):
        return self.rand + self.pubkey + self.signature 
    
    def get_len(self):
        return 384

class RevealRandomTransaction():
    def parse(self, raw_data):
        self.commit_hash = raw_data[:32]
        self.key = raw_data[32:128 + 32]
    
    def pack(self):
        raw = self.commit_hash
        raw += self.key
        return raw
    
    def get_len(self):
        return 32 + 128

    def get_hash(self):
        return SHA256.new(self.pack())        