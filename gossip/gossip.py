import struct
from chain.signed_block import SignedBlock

"""
Gossip message used for off chain data transfer.
Gossip can be POSITIVE or NEGATIVE
gossip- (NEGATIVE GOSSIP) is structured broadcast request send to validator about absent block in X time_slot
gossip+ (POSITIVE GOSSIP) is structured broadcast data send to requester with block in X time_slot

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
- validator node DO NOT listen positive gossip

send negative gossip- rule
- negative gossip sends when block not received on time_slot finished

send positive gossip+ rule
- positive gossip can be sent ONLY by validator node by negative gossip- request received

"""


# negative gossip base class
class NegativeGossip:
    def __init__(self):
        # node signature
        self.node_signature = None
        # node public key (gossip request sender address)
        self.node_public_key = None
        # current timestamp
        self.timestamp = None
        # block number
        self.number_of_block = None

    def parse(self, raw_data):
        self.node_signature = int.from_bytes(raw_data[:128], byteorder='big')
        self.node_public_key = raw_data[128:344]
        self.timestamp = struct.unpack_from("I", raw_data[344:348])[0]
        self.number_of_block = int.from_bytes(raw_data[348:352], byteorder='big')

    def pack(self):
        return self.node_signature + \
               self.node_public_key + \
               self.timestamp + \
               self.number_of_block


# positive gossip base class
class PositiveGossip:
    def __init__(self):
        # node signature
        self.node_signature = None
        # node public key (gossip request sender address)
        self.node_public_key = None
        # current timestamp
        self.timestamp = None
        # returned block by number
        self.block = None

    def parse(self, raw_data):
        self.node_signature = int.from_bytes(raw_data[:128], byteorder='big')
        self.node_public_key = raw_data[128:344]
        self.timestamp = struct.unpack_from("I", raw_data[344:348])[0]
        self.block = SignedBlock().parse(raw_data=raw_data[348:])

    def pack(self):
        return self.node_signature + \
               self.node_public_key + \
               self.timestamp + \
               self.block

