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
        elif tx_type == Type.REVEAL:
            tx = RevealRandomTransaction()
        else:
            assert False, "Cannot parse unknown transaction type"
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
        self.pubkey = raw_data[128:344]
        self.signature = int.from_bytes(raw_data[344:472], byteorder='big')
    
    def pack(self):
        return self.rand + self.pubkey + self.signature.to_bytes(128, byteorder='big')
    
    def get_len(self):
        return 472

class RevealRandomTransaction():
    def parse(self, raw_data):
        self.commit_hash = raw_data[:32]
        key_length = struct.unpack_from("H", raw_data, 32)[0]
        self.len = 34 + key_length
        self.key = raw_data[34:self.len]
    
    def pack(self):
        raw = self.commit_hash
        raw += struct.pack("H", len(self.key))
        raw += self.key
        return raw
    
    def get_len(self):
        return self.len

    def get_hash(self):
        return SHA256.new(self.pack())        