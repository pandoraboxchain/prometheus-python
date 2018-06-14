from Crypto.Hash import SHA256
import struct

class Type():
    PUBLIC = 0
    RANDOM = 1
    PRIVATE = 2

class TransactionParser():
    def parse(raw_data):
        tx_type = struct.unpack_from("B", raw_data)[0]
        if tx_type == Type.PUBLIC:
            tx = PublicKeyTransaction()
        elif tx_type == Type.RANDOM:
            tx = SplitRandomTransaction()
        elif tx_type == Type.PRIVATE:
            tx = PrivateKeyTransaction()
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
        else:
            assert False, "Cannot pack unknown transaction type"
        raw += tx.pack()
        return raw

class CommitRandomTransaction():
    def get_hash(self):
        return SHA256.new(self.rand + self.pubkey).digest()

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