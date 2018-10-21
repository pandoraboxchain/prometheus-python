from hashlib import sha256
from serialization.serializer import Serializer, Deserializer

# this is payment simulation
# no payment correctness checking is done since sole purpose of this transactions
# is to verify merge transaction conflict resolution
# this transaction has no signature for now

#TODO think if multiple input can cause problems to conflict resolution mechanism

class PaymentTransaction:
    def __init__(self):
        self.input = None  # transaction hash
        self.number = None
        self.outputs = None # transaction hash
        self.amounts = None  
        self.len = None

    def get_hash(self):
        return sha256(self.pack()).digest()

    def parse(self, raw_data):
        deserializer = Deserializer(raw_data)
        self.input = deserializer.parse_hash()
        self.number = deserializer.parse_u8()
        
        output_count = deserializer.parse_u8()
        self.outputs = []
        for _ in range(output_count):
            self.outputs.append(deserializer.parse_hash())
        
        self.amounts = []
        for _ in range(output_count): #amount count must be the same as output count
            self.amounts.append(deserializer.parse_u32())
        self.len = deserializer.len
    
    def pack(self):
        assert len(self.outputs) == len(self.amounts), "Outputs count must match amounts count"
        raw = self.input
        raw += Serializer.write_u8(self.number)
        raw += Serializer.write_u8(len(self.outputs))        
        for output in self.outputs:
            raw += output
        for amount in self.amounts:
            raw += Serializer.write_u32(amount)
        return raw

    def get_len(self):
        return self.len