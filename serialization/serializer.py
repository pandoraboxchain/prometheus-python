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
    def write_u32(u32):
        return struct.pack("I", u32)

    @staticmethod
    def write_i32(i32):
        return int.to_bytes(i32, length=4, byteorder='big')


class Deserializer:
    def __init__(self, data):
        self.data = data

    def read_and_move(self, byte_count):
        parsed = self.data[:byte_count]
        self.data = self.data[byte_count:]
        return parsed

    def parse_pubkey(self):
        return self.read_and_move(216)

    def parse_signature(self):
        return self.read_and_move(128)
    
    def parse_timestamp(self):
        return self.parse_u32()

    def parse_u8(self):
        parsed = struct.unpack_from("B", self.data)[0]
        self.data = self.data[1:]
        return parsed

    def parse_u16(self):
        parsed = struct.unpack_from("H", self.data)[0]
        self.data = self.data[2:]
        return parsed

    def parse_u32(self):
        parsed = struct.unpack_from("I", self.data)[0]
        self.data = self.data[4:]
        return parsed

