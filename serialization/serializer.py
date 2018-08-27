import struct


class Serializer:
    def __init__(self):
        self.data = bytearray()

    @staticmethod
    def write_signature(signature):
        return signature.to_bytes(128, byteorder='big')

    @staticmethod
    def write_timestamp(timestamp):
        return Serializer.write_u32(timestamp)

    @staticmethod
    def write_private_key(private_key):
        raw = Serializer.write_u16(len(private_key))
        raw += private_key
        return raw

    @staticmethod
    def write_encrypted_data(data):
        raw = Serializer.write_u8(len(data))
        raw += data
        return raw

    @staticmethod
    def write_u8(u8):
        return struct.pack("B", u8)

    @staticmethod
    def write_u16(u16):
        return struct.pack("H", u16)

    @staticmethod
    def write_u32(u32):
        return struct.pack("I", u32)

    @staticmethod
    def write_i32(i32):
        return int.to_bytes(i32, length=4, byteorder='big')


class Deserializer:
    def __init__(self, data):
        self.data = data
        self.len = 0

    def read_and_move(self, byte_count):
        parsed = self.data[:byte_count]
        self.data = self.data[byte_count:]
        self.len += byte_count
        return parsed

    def parse_pubkey(self):
        return self.read_and_move(216)

    def parse_signature(self):
        signature_bytes = self.read_and_move(128)
        return int.from_bytes(signature_bytes, byteorder='big')
    
    def parse_timestamp(self):
        return self.parse_u32()

    #sometimes encrypted value can be 127 or 128 bytes in 32-byte RSA
    def parse_encrypted_data(self):
        length = self.parse_u8()    #255 bytes max
        return self.read_and_move(length)

    def parse_hash(self):
        return self.read_and_move(32)

    def parse_u8(self):
        parsed = struct.unpack_from("B", self.data)[0]
        self.data = self.data[1:]
        self.len += 1
        return parsed

    def parse_u16(self):
        parsed = struct.unpack_from("H", self.data)[0]
        self.data = self.data[2:]
        self.len += 2
        return parsed

    def parse_u32(self):
        parsed = struct.unpack_from("I", self.data)[0]
        self.data = self.data[4:]
        self.len += 4
        return parsed

    def parse_private_key(self):
        key_length = self.parse_u16()
        return self.read_and_move(key_length)

    # returns amount of read bytes
    def get_len(self):
        return self.len

