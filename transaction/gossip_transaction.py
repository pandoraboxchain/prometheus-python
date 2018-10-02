from hashlib import sha256
from serialization.serializer import Serializer, Deserializer

"""
Gossip message used for on/off chain data transfer.
Gossip can be POSITIVE or NEGATIVE
gossip- (NEGATIVE GOSSIP) is structured broadcast request send to validator about absent block in X time_slot
gossip+ (POSITIVE GOSSIP) is structured broadcast data send to requester with block tx_hash in X time_slot

gossip_penalty (PENALTY GOSSIP) includes positive and negative gossip tx hashes

gossip validation rules
- gossip can be sent by every node (simple_node, validator)
- gossip must contains:
    - sender public key
    - sender signature
    - asked block number/existing block
    - current timestamp

- negative gossip can be broadcast only once by one node per time_slot
- positive gossip must be broadcast by ALL nodes
  (3 same positive gossips by different senders means that this is correct block)
- every node (except sender) listen positive gossip validate it and add to DAG if block not exist

send negative gossip- rule
- negative gossip sends when block not received on time_slot finished

send positive gossip+ rule
- positive gossip can be sent ONLY by validator node by negative gossip- request received

"""


# negative gossip base class
class NegativeGossipTransaction:
    def __init__(self):
        # node signature
        self.signature = None
        # node public key (gossip request sender address)
        self.pubkey = None
        # current timestamp
        self.timestamp = None
        # expected block number
        self.number_of_block = None
        # anchor block hash
        self.anchor_block_hash = None
        # tx length
        self.len = None

    def parse(self, raw_data):
        deserializer = Deserializer(raw_data)
        self.signature = deserializer.parse_signature()
        self.pubkey = deserializer.parse_pubkey()
        self.timestamp = deserializer.parse_timestamp()
        self.number_of_block = deserializer.parse_u32()
        self.anchor_block_hash = deserializer.parse_hash()
        self.len = deserializer.get_len()

    def pack(self):
        return Serializer.write_signature(self.signature) + \
               self.pack_fields()

    def pack_fields(self):
        return self.pubkey + \
               Serializer.write_timestamp(self.timestamp) + \
               Serializer.write_u32(self.number_of_block) + \
               self.anchor_block_hash

    def get_len(self):
        return self.len

    def get_hash(self):
        return sha256(self.pack_fields()).digest()


# positive gossip base class
class PositiveGossipTransaction:
    def __init__(self):
        # node signature
        self.signature = None
        # node public key (gossip request sender address)
        self.pubkey = None
        # current timestamp
        self.timestamp = None
        # returned block hash by number
        self.block_hash = None
        # tx length
        self.len = None

    def parse(self, raw_data):
        deserializer = Deserializer(raw_data)
        self.signature = deserializer.parse_signature()
        self.pubkey = deserializer.parse_pubkey()
        self.timestamp = deserializer.parse_timestamp()
        self.block_hash = deserializer.parse_hash()
        self.len = deserializer.get_len()

    def pack(self):
        return Serializer.write_signature(self.signature) + \
               self.pack_fields()

    def pack_fields(self):
        return self.pubkey + \
               Serializer.write_timestamp(self.timestamp) + \
               self.block_hash

    def get_hash(self):
        return sha256(self.pack_fields()).digest()

    def get_len(self):
        return self.len


# penalty gossip base class
class PenaltyGossipTransaction:

    def __init__(self):
        self.conflicts = []
        self.signature = None
        # current timestamp
        self.timestamp = None
        self.len = None

    def parse(self, raw_data):
        deserializer = Deserializer(raw_data)
        conflict_count = deserializer.parse_u8()
        self.conflicts = []
        for _ in range(0, conflict_count):
            conflict = deserializer.parse_hash()
            self.conflicts.append(conflict)
        self.signature = deserializer.parse_signature()
        self.timestamp = deserializer.parse_timestamp()
        self.len = deserializer.len

    def pack(self):
        raw = self.pack_conflicts()
        raw += Serializer.write_signature(self.signature) + \
               Serializer.write_timestamp(self.timestamp)
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

