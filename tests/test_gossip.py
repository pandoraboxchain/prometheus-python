import unittest

from node.behaviour import Behaviour
from chain.block_factory import BlockFactory
from chain.epoch import Epoch
from node.block_signers import BlockSigners
from node.node import Node
from node.node_api import NodeApi
from node.validators import Validators
from crypto.keys import Keys
from crypto.private import Private
from tools.time import Time
from transaction.gossip_transaction import PositiveGossipTransaction, NegativeGossipTransaction, \
    PenaltyGossipTransaction

"""
    Simple case where node1 create but not broadcast block
     - two nodes will have not block 2 in third timeslot
     - on step node0() gossips will launch and derive block to every node which do not have block
     - no step node2() (is validator on test timeslot) it already must have previous timeslote block

    Hard case where VALIDATOR node have no previous timeslot block
    So it need 2 independent on time steps for provide negative gossip logic and create new block for validator

    Very HARD case when VALIDATOR NODE have no previous block and have two top bloks!!!!
    - send two negative gossips ?
    - add anchor hash to negative gossip for requested block ?
    - невозможно провести валидацию негативных госипов кроме как по локлаьному дагу но только раз в блок
    """


class TestGossip(unittest.TestCase):

    def test_parse_pack_gossip_positive(self):
        private = Private.generate()
        original = PositiveGossipTransaction()
        original.pubkey = Private.publickey(private)
        original.timestamp = Time.get_current_time()

        block = BlockFactory.create_block_with_timestamp([], timestamp=original.timestamp)
        original.block_hash = BlockFactory.sign_block(block, private).get_hash()
        original.signature = Private.sign(original.get_hash(), private)

        raw = original.pack()
        restored = PositiveGossipTransaction()
        restored.parse(raw)

        self.assertEqual(original.get_hash(), restored.get_hash())

    def test_parse_pack_gossip_negative(self):
        private = Private.generate()
        original = NegativeGossipTransaction()
        original.pubkey = Private.publickey(private)
        original.timestamp = Time.get_current_time()
        original.number_of_block = 47

        block = BlockFactory.create_block_with_timestamp([], timestamp=original.timestamp)
        original.anchor_block_hash = block.get_hash()
        original.signature = Private.sign(original.get_hash(), private)

        raw = original.pack()
        restored = NegativeGossipTransaction()
        restored.parse(raw)

        self.assertEqual(original.get_hash(), restored.get_hash())

    def test_pack_parse_penalty_gossip_transaction(self):
        private = Private.generate()
        original = PenaltyGossipTransaction()
        original.timestamp = Time.get_current_time()
        block = BlockFactory.create_block_with_timestamp([], timestamp=original.timestamp)

        gossip_positive_tx = PositiveGossipTransaction()
        gossip_positive_tx.pubkey = Private.publickey(private)
        gossip_positive_tx.timestamp = Time.get_current_time()
        gossip_positive_tx.block_hash = BlockFactory.sign_block(block, private).get_hash()
        gossip_positive_tx.signature = Private.sign(original.get_hash(), private)

        gossip_negative_tx = NegativeGossipTransaction()
        gossip_negative_tx.pubkey = Private.publickey(private)
        gossip_negative_tx.timestamp = Time.get_current_time()
        gossip_negative_tx.number_of_block = 47
        gossip_negative_tx.anchor_block_hash = block.get_hash()
        gossip_negative_tx.signature = Private.sign(original.get_hash(), private)

        original.conflicts = [gossip_positive_tx.get_hash(), gossip_negative_tx.get_hash()]
        original.signature = Private.sign(original.get_hash(), private)

        original.block_hash = BlockFactory.sign_block(block, private).get_hash()

        raw = original.pack()
        restored = PenaltyGossipTransaction()
        restored.parse(raw)

        self.assertEqual(original.get_hash(), restored.get_hash())

    def test_send_negative_gossip(self):
        Time.use_test_time()
        Time.set_current_time(1)

        private_keys = BlockSigners()
        private_keys = private_keys.block_signers

        validators = Validators()
        validators.validators = Validators.read_genesis_validators_from_file()
        validators.signers_order = [0] + [1] * Epoch.get_duration()
        validators.randomizers_order = [0] * Epoch.get_duration()

        network = NodeApi()
        behavior = Behaviour()
        behavior.malicious_skip_block = True
        node0 = Node(genesis_creation_time=1,
                     node_id=0,
                     network=network,
                     block_signer=private_keys[0],
                     validators=validators,
                     behaviour=behavior)
        network.register_node(node0)

        node1 = Node(genesis_creation_time=1,
                     node_id=1,
                     network=network,
                     block_signer=private_keys[1],
                     validators=validators,
                     behaviour=Behaviour())
        network.register_node(node1)

        Time.advance_to_next_timeslot()
        node0.step()
        self.assertEqual(len(node0.dag.blocks_by_number), 1)  # ensure that block skipped by node0
        node1.step()
        self.assertEqual(len(node0.dag.blocks_by_number), 1)  # ensure that block not received by node1

        Time.advance_to_next_timeslot()
        # on next step node0 broadcast negative gossip
        node0.step()
        # and not include it to (node0) self.mempool
        self.assertEqual(len(node0.mempool.gossips), 0)
        # assume that negative gossip broadcasted and placed to node1 mempool
        self.assertEqual(len(node1.mempool.gossips), 1)
# -----------------------------------
        # on next step node 1 will send negative gossip
        # node1 MUST create and sign block which contain negative gossip and broadcast it
        node1.step()
        # node1 in it's step broadcast(GOSSIP-) and at the same time SKIP!!! method
        # self.try_to_sign_block(current_block_number)

        # A second step is needed to create and sign a block within the same time slot
        Time.advance_time(1)  # !!! -----> advance time by 1 second (DO NOT CHANGE TIMESLOT) !!!
        node1.step()
# -----------------------------------
        # verify that node1 make block broadcast
        self.assertEqual(len(node1.dag.blocks_by_number), 2)
        # verify that node0 receive new block
        self.assertEqual(len(node0.dag.blocks_by_number), 2)
        # verify that negative gossip transaction is in block
        system_txs = node0.dag.blocks_by_number[2][0].block.system_txs
        self.assertTrue(NegativeGossipTransaction.__class__, system_txs[3].__class__)

    def test_send_positive_gossip(self):
        Time.use_test_time()
        Time.set_current_time(1)

        private_keys = BlockSigners()
        private_keys = private_keys.block_signers

        validators = Validators()
        validators.validators = Validators.read_genesis_validators_from_file()
        validators.signers_order = [0] + [1] + [2] * Epoch.get_duration()
        validators.randomizers_order = [0] * Epoch.get_duration()

        network = NodeApi()

        node0 = Node(genesis_creation_time=1,
                     node_id=0,
                     network=network,
                     block_signer=private_keys[0],
                     validators=validators,
                     behaviour=Behaviour())
        network.register_node(node0)

        behavior = Behaviour()
        behavior.transport_cancel_block_broadcast = True
        node1 = Node(genesis_creation_time=1,
                     node_id=1,
                     network=network,
                     block_signer=private_keys[1],
                     validators=validators,
                     behaviour=behavior)
        network.register_node(node1)

        node2 = Node(genesis_creation_time=1,
                     node_id=2,
                     network=network,
                     block_signer=private_keys[2],
                     validators=validators,
                     behaviour=Behaviour())
        network.register_node(node2)
        # it is necessary that it would work for any count() of nodes
        # and ANY count() of listeners of current node in one timeslot
        # WARNING - IT CAN BE MINIMIZED BY NODE_LISTENERS_COUNT()
        # | max count() of get_block_by_hash() request's RESPONSE by timeslot (where RESPONSE.COUNT() == 'x')

        Time.advance_to_next_timeslot()  # current block number 1
        node0.step()  # create and sign block
        node1.step()
        node2.step()
        self.assertTrue(len(node0.dag.blocks_by_number) == 2, True)
        self.assertTrue(len(node1.dag.blocks_by_number) == 2, True)
        self.assertTrue(len(node2.dag.blocks_by_number) == 2, True)
        # asset that node0 create block number 2
        #
        Time.advance_to_next_timeslot()  # current block number 2
        node0.step()
        node1.step()  # skip broadcasting block
        node2.step()
        self.assertTrue(len(node0.dag.blocks_by_number) == 2, True)
        self.assertTrue(len(node1.dag.blocks_by_number) == 3, True)
        self.assertTrue(len(node2.dag.blocks_by_number) == 2, True)
        # assert that block 3 created on node1 but not broadcasted to node0 and node2

        Time.advance_to_next_timeslot()  # current block number 3
        node0.step()  # send negative gossip for block 3
        self.assertTrue(len(node0.dag.blocks_by_number) == 3, True)
        # performs broadcast (gossip-)
        # all nodes accept sender and handle (gossip-) tx ---> self.mempool()
        # check for block by slot number and IF IT'S EXIST ----> broadcast (gossip+)
        # every node which receive (gossip+) ----> self.mempool()
        # check local DAG for block exist ----> if not request it by DIRECT_REQUEST to node from which (gossip+) income
        # node MUST answer to min 50% of connected listeners requests(network.get_block_by_hash()).count()

        node1.step()  # send possitive gossip block 3 and (block 3 by block request)
        self.assertTrue(len(node1.dag.blocks_by_number) == 3, True)
        self.assertTrue(len(node2.dag.blocks_by_number) == 3, True)

        node2.step()  # send negative gossip for block 3 create and sign block (with negative gossips) block number 4
        self.assertTrue(len(node0.dag.blocks_by_number) == 4, True)
        self.assertTrue(len(node1.dag.blocks_by_number) == 4, True)
        self.assertTrue(len(node2.dag.blocks_by_number) == 4, True)

        # at such emulation if the validator is not the first who sent a negative state
        # By the time the block is signed, in turn, it will already have a full and valid dag

        # providing request for gossip- will delay creation and signing of the block by the VALIDATOR node
        # but in this case it is not required (will be checked in the next test)

        Time.advance_to_next_timeslot()
        node0.step()
        node1.step()
        node2.step()
        self.assertTrue(len(node0.dag.blocks_by_number) == 5, True)
        self.assertTrue(len(node1.dag.blocks_by_number) == 5, True)
        self.assertTrue(len(node2.dag.blocks_by_number) == 5, True)
        # assert that next block is correctly created by next node

    def test_send_negative_gossip_by_validator(self):
        Time.use_test_time()
        Time.set_current_time(1)

        private_keys = BlockSigners()
        private_keys = private_keys.block_signers

        validators = Validators()
        validators.validators = Validators.read_genesis_validators_from_file()
        validators.signers_order = [0] + [1] + [2] * Epoch.get_duration()
        validators.randomizers_order = [0] * Epoch.get_duration()

        network = NodeApi()

        node0 = Node(genesis_creation_time=1,
                     node_id=0,
                     network=network,
                     block_signer=private_keys[0],
                     validators=validators,
                     behaviour=Behaviour())
        network.register_node(node0)

        behavior = Behaviour()
        behavior.transport_cancel_block_broadcast = True
        node1 = Node(genesis_creation_time=1,
                     node_id=1,
                     network=network,
                     block_signer=private_keys[1],
                     validators=validators,
                     behaviour=behavior)
        network.register_node(node1)

        node2 = Node(genesis_creation_time=1,
                     node_id=2,
                     network=network,
                     block_signer=private_keys[2],
                     validators=validators,
                     behaviour=Behaviour())
        network.register_node(node2)
        # same config from prev. test

        Time.advance_to_next_timeslot()  # current block number 1
        node0.step()  # create and sign block
        node1.step()
        node2.step()
        self.assertTrue(len(node0.dag.blocks_by_number) == 2, True)
        self.assertTrue(len(node1.dag.blocks_by_number) == 2, True)
        self.assertTrue(len(node2.dag.blocks_by_number) == 2, True)
        # asset that node0 create block number 2
        #
        Time.advance_to_next_timeslot()  # current block number 2
        node0.step()
        node1.step()  # skip broadcasting block
        node2.step()
        self.assertTrue(len(node0.dag.blocks_by_number) == 2, True)
        self.assertTrue(len(node1.dag.blocks_by_number) == 3, True)
        self.assertTrue(len(node2.dag.blocks_by_number) == 2, True)
        # assert that block 3 created on node1 but not broadcasted to node0 and node2
        #
        Time.advance_to_next_timeslot()  # current block number 3
        node2.step()  # MAKE FIRST STEP BY CURRENT TIMESLOT VALIDATOR (BLOCK SIGNER)
        self.assertTrue(len(node0.dag.blocks_by_number) == 3, True)
        self.assertTrue(len(node1.dag.blocks_by_number) == 3, True)
        self.assertTrue(len(node2.dag.blocks_by_number) == 3, True)
        # assert that all listeners nodes receive missed block`s
        Time.advance_time(1)  # ADVANCE TIME BY ONE SECOND TIMESLOT SAME
        node2.step()
        self.assertTrue(len(node0.dag.blocks_by_number) == 4, True)
        self.assertTrue(len(node1.dag.blocks_by_number) == 4, True)
        self.assertTrue(len(node2.dag.blocks_by_number) == 4, True)
        # assert that  node 2 create, sign, broadcast and deliver block number 4
        # for certainty we will make some more steps by NOT VALIDATOR nodes's
        node0.step()
        node1.step()
        node1.step()
        node0.step()
        node0.step()

        Time.advance_to_next_timeslot()  # current block number 4
        node0.step()
        node1.step()
        node2.step()
        # step by all and validate block 5
        self.assertTrue(len(node0.dag.blocks_by_number) == 5, True)
        self.assertTrue(len(node1.dag.blocks_by_number) == 5, True)
        self.assertTrue(len(node2.dag.blocks_by_number) == 5, True)


