import unittest

from node.behaviour import Behaviour
from chain.block_factory import BlockFactory
from chain.epoch import Epoch
from chain.params import Round
from node.block_signers import BlockSigners
from node.node import Node
from node.node_api import NodeApi
from node.validators import Validators
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
        validators.signers_order = [0, 1] * (Epoch.get_duration() // 2)
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
        # and include! it to (node0) self.mempool
        self.assertEqual(len(node0.mempool.gossips), 1)
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
        validators.signers_order = [0,1,2] * 10
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

        # after node0 step and broadcast negative gossip
        # node 2 MUST contains this tx in mempool
        # current solution is to broadcast negative gossip IF current mempool negative gossip
        # count is < than 5 (system parameter ZETA) -----> #TODO check in next test
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

    # perform testing ZETA by malicious_skip_block in network of min nodes < ZETA
    def test_negative_gossip_by_zeta(self):
        Time.use_test_time()
        Time.set_current_time(1)

        private_keys = BlockSigners()
        private_keys = private_keys.block_signers

        validators = Validators()
        validators.validators = Validators.read_genesis_validators_from_file()
        validators.signers_order = [0] + [1] + [2] + [3] + [4] + [5] * Epoch.get_duration()
        validators.randomizers_order = [0] * Epoch.get_duration()

        network = NodeApi()

        node0 = Node(genesis_creation_time=1,
                     node_id=0,
                     network=network,
                     block_signer=private_keys[0],
                     validators=validators,
                     behaviour=Behaviour())
        network.register_node(node0)

        behavior = Behaviour()  # this node malicious skip block
        behavior.malicious_skip_block = True
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

        node3 = Node(genesis_creation_time=1,
                     node_id=3,
                     network=network,
                     block_signer=private_keys[3],
                     validators=validators,
                     behaviour=Behaviour())
        network.register_node(node3)

        node4 = Node(genesis_creation_time=1,
                     node_id=4,
                     network=network,
                     block_signer=private_keys[4],
                     validators=validators,
                     behaviour=Behaviour())
        network.register_node(node4)

        node5 = Node(genesis_creation_time=1,
                     node_id=5,
                     network=network,
                     block_signer=private_keys[5],
                     validators=validators,
                     behaviour=Behaviour())
        network.register_node(node5)

        Time.advance_to_next_timeslot()  # current block number 1
        node0.step()    # create and sign block
        node1.step()
        node2.step()
        node3.step()
        node4.step()
        node5.step()
        # validate block created and broadcasted
        self.list_validator(network.nodes, ['dag.blocks_by_number.length'], 2)

        Time.advance_to_next_timeslot()  # current block number 1
        node0.step()
        node1.step()    # skip block creation
        node2.step()
        node3.step()
        node4.step()
        node5.step()
        # validate block NOT created and NOT broadcasted
        self.list_validator(network.nodes, ['dag.blocks_by_number.length'], 2)

        Time.advance_to_next_timeslot()  # current block number 2
        # for now all chain do not have block from previous timeslot
        node0.step()  # broadcast negative gossip
        # all nodes handle negative gossips by node0
        # not broadcast to self (ADD TO MEMPOOL before broadcast)
        self.list_validator(network.nodes, ['mempool.gossips.length'], 1)

        node1.step()  # broadcast negative gossip
        self.list_validator(network.nodes, ['mempool.gossips.length'], 2)

        node2.step()  # broadcast negative gossip AND skip block signing for current step !!!
        node3.step()  # broadcast negative gossip
        node4.step()  # broadcast negative gossip
        node5.step()  # VALIDATE 5 NEGATIVE GOSSIPS AND DO NOT BROADCAST ANOTHER ONE (current ZETA == 5)
        self.list_validator(network.nodes, ['mempool.gossips.length'], 5)

        # duplicate gossips tx will NOT include to mempool !
        # if node already send negative gossip IT NOT broadcast it again !
        # if node already have x < ZETA (x - different negative gossips by block count) IT NOT broadcast it again !
        Time.advance_time(1)  # advance time by one second in current timeslot
        # make steps by nodes
        node0.step()  #
        node1.step()  #
        # steel 5 negative gossips (from 0,1,2,3,4) on all nodes (add validation ?)
        self.list_validator(network.nodes, ['mempool.gossips.length'], 5)

        node2.step()  # CREATE, SIGN, BROADCAST block (block by node1 not exist)

        # all nodes handle new block
        self.list_validator(network.nodes, ['dag.blocks_by_number.length'], 3)
        # gossips cleaned from mem pool by block handling
        self.list_validator(network.nodes, ['mempool.gossips.length'], 0)

        node3.step()  #
        node4.step()  #
        node5.step()  #

        #  provide validation for next normal block and FOR GOSSIPS is NOT in mempool after next block
        Time.advance_to_next_timeslot()  # current block number 3
        node0.step()  #
        node1.step()  #
        node2.step()  #
        node3.step()  # must create and sign and broadcast block (all gossips MUST be mined and erased from mempool)
        node4.step()  #
        node5.step()  #

        # after node2 step
        self.list_validator(network.nodes, ['dag.blocks_by_number.length'], 4)
        self.list_validator(network.nodes, ['mempool.gossips.length'], 0)

    def test_maliciously_send_negative_gossip(self):
        Time.use_test_time()
        Time.set_current_time(1)

        private_keys = BlockSigners()
        private_keys = private_keys.block_signers

        validators = Validators()
        validators.validators = Validators.read_genesis_validators_from_file()
        validators.signers_order = [0,1,2,3,4,5] * 4
        validators.randomizers_order = [0] * Epoch.get_duration()

        network = NodeApi()

        node0 = Node(genesis_creation_time=1,
                     node_id=0,
                     network=network,
                     block_signer=private_keys[0],
                     validators=validators,
                     behaviour=Behaviour())

        network.register_node(node0)

        behavior = Behaviour()  # this node maliciously send negative gossip
        behavior.malicious_send_negative_gossip_count = 1
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

        node3 = Node(genesis_creation_time=1,
                     node_id=3,
                     network=network,
                     block_signer=private_keys[3],
                     validators=validators,
                     behaviour=Behaviour())
        network.register_node(node3)

        node4 = Node(genesis_creation_time=1,
                     node_id=4,
                     network=network,
                     block_signer=private_keys[4],
                     validators=validators,
                     behaviour=Behaviour())
        network.register_node(node4)

        node5 = Node(genesis_creation_time=1,
                     node_id=5,
                     network=network,
                     block_signer=private_keys[5],
                     validators=validators,
                     behaviour=Behaviour())
        network.register_node(node5)

        Time.advance_to_next_timeslot()  # current block number 1
        node0.step()  # create and sign block
        # validate block created and broadcasted
        # validate mempool is empty
        # validate tx by hash is empty
        self.list_validator(network.nodes, ['dag.blocks_by_number.length'], 2)
        self.list_validator(network.nodes, ['mempool.gossips.length'], 0)

        node1.step()  # ! maliciously sand negative gossip (request by genesis 0 block)
        # all node receive negative gossip and send positive except node1
        # ( - do not send positive gossip if your send negative)
        # txs for now only in mempool (not in block)
        self.list_validator(network.nodes, ['dag.blocks_by_number.length'], 2)
        # all nodes has 1-gossip and 5+gossips (1-gossip and 5+gossip from (0,2,3,4,5))
        self.list_validator(network.nodes, ['mempool.gossips.length'], 6)

        node2.step()
        node3.step()
        node4.step()
        node5.step()
        # after all steps situation same
        self.list_validator(network.nodes, ['dag.blocks_by_number.length'], 2)
        self.list_validator(network.nodes, ['mempool.gossips.length'], 6)

        Time.advance_to_next_timeslot()  # current block number 2
        node0.step()  # do nothing
        node1.step()  # is validator by order (need to marge mempool and provide block)
        # возможно добавить проверку на малишес скип блок в добавок ?
        # (по идеи все должны еще раз обменятся госипами и уже не найти блок 2)
        # (в таком случае следующий валидатор должен смерджить все и отправить блок)
        # (нода 1 должна быть исключена из списка валидаторов ?)
        # after node create and sign block all node clean its mem pool
        # here we have 3 blocks, empty mem pools, and transactions in dag.transaction_by_hash
        self.list_validator(network.nodes, ['dag.blocks_by_number.length'], 3)
        self.list_validator(network.nodes, ['mempool.gossips.length'], 0)
        # 6 - gossips (1 negative 5 positive) and 3 - public keys = 9

        node2.step()
        node3.step()
        node4.step()
        node5.step()
        # validate that all keeps the same
        self.list_validator(network.nodes, ['dag.blocks_by_number.length'], 3)
        self.list_validator(network.nodes, ['mempool.gossips.length'], 0)

        Time.advance_to_next_timeslot()  # current block number 3
        node0.step()  # do nothing
        node1.step()  # do nothing
        node2.step()  # provide block
        node3.step()
        node4.step()
        node5.step()

        # validate new block by node2
        self.list_validator(network.nodes, ['dag.blocks_by_number.length'], 4)

    def test_maliciously_send_positive_gossip(self):
        Time.use_test_time()
        Time.set_current_time(1)

        private_keys = BlockSigners()
        private_keys = private_keys.block_signers

        validators = Validators()
        validators.validators = Validators.read_genesis_validators_from_file()
        validators.signers_order = [0,1,2,3,4,5] * 4
        validators.randomizers_order = [0] * Epoch.get_duration()

        network = NodeApi()

        node0 = Node(genesis_creation_time=1,
                     node_id=0,
                     network=network,
                     block_signer=private_keys[0],
                     validators=validators,
                     behaviour=Behaviour())

        network.register_node(node0)

        behavior = Behaviour()  # this node maliciously send positive gossip
        behavior.malicious_send_positive_gossip_count = 1
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

        node3 = Node(genesis_creation_time=1,
                     node_id=3,
                     network=network,
                     block_signer=private_keys[3],
                     validators=validators,
                     behaviour=Behaviour())
        network.register_node(node3)

        node4 = Node(genesis_creation_time=1,
                     node_id=4,
                     network=network,
                     block_signer=private_keys[4],
                     validators=validators,
                     behaviour=Behaviour())
        network.register_node(node4)

        node5 = Node(genesis_creation_time=1,
                     node_id=5,
                     network=network,
                     block_signer=private_keys[5],
                     validators=validators,
                     behaviour=Behaviour())
        network.register_node(node5)

        Time.advance_to_next_timeslot()  # current block number 1
        node0.step()  # create and sign block
        # validate block created and broadcasted
        # validate mempool is empty
        self.list_validator(network.nodes, ['dag.blocks_by_number.length'], 2)
        self.list_validator(network.nodes, ['mempool.gossips.length'], 0)

        node1.step()  # ! maliciously sand positive gossip (request by genesis 0 block)
        # all node receive positive gossip
        # txs for now only in mempool (not in block)
        self.list_validator(network.nodes, ['dag.blocks_by_number.length'], 2)
        # all nodes has 1+gossips
        self.list_validator(network.nodes, ['mempool.gossips.length'], 1)

        node2.step()
        node3.step()
        node4.step()
        node5.step()
        # after all steps situation same
        self.list_validator(network.nodes, ['dag.blocks_by_number.length'], 2)
        self.list_validator(network.nodes, ['mempool.gossips.length'], 1)

        Time.advance_to_next_timeslot()  # current block number 2
        node0.step()  # do nothing
        node1.step()  # is validator by order (need to marge mempool and provide block)
        # возможно добавить проверку на малишес скип блок в добавок ?
        # (по идеи все должны еще раз обменятся госипами и уже не найти блок 2)
        # (в таком случае следующий валидатор должен смерджить все и отправить блок)
        # (нода 1 должна быть исключена из списка валидаторов ?)
        # after node create and sign block all node clean its mem pool
        # here we have 3 blocks, empty mem pools, and transaction in dag.transaction_by_hash
        self.list_validator(network.nodes, ['dag.blocks_by_number.length'], 3)
        self.list_validator(network.nodes, ['mempool.gossips.length'], 0)

        node2.step()
        node3.step()
        node4.step()
        node5.step()
        # validate that all keeps the same
        self.list_validator(network.nodes, ['dag.blocks_by_number.length'], 3)
        self.list_validator(network.nodes, ['mempool.gossips.length'], 0)

        Time.advance_to_next_timeslot()  # current block number 3
        node0.step()  # do nothing
        node1.step()  # do nothing
        node2.step()  # provide block
        node3.step()
        node4.step()
        node5.step()

        # validate new block by node2
        self.list_validator(network.nodes, ['dag.blocks_by_number.length'], 4)

    def test_maliciously_send_negative_and_positive_gossip(self):
        Time.use_test_time()
        Time.set_current_time(1)

        private_keys = BlockSigners()
        private_keys = private_keys.block_signers

        validators = Validators()
        validators.validators = Validators.read_genesis_validators_from_file()
        validators.signers_order = [0] + [1] + [2] + [3] + [4] + [5] * Epoch.get_duration()
        validators.randomizers_order = [0] * Epoch.get_duration()

        signer_index = 0
        for i in Epoch.get_round_range(1, Round.PRIVATE):
            validators.signers_order[i] = signer_index
            signer_index += 1

        network = NodeApi()

        node0 = Node(genesis_creation_time=1,
                     node_id=0,
                     network=network,
                     block_signer=private_keys[0],
                     validators=validators,
                     behaviour=Behaviour())

        network.register_node(node0)

        behavior = Behaviour()  # this node maliciously send positive and negative gossip
        behavior.malicious_send_negative_gossip_count = 1
        behavior.malicious_send_positive_gossip_count = 1
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

        node3 = Node(genesis_creation_time=1,
                     node_id=3,
                     network=network,
                     block_signer=private_keys[3],
                     validators=validators,
                     behaviour=Behaviour())
        network.register_node(node3)

        node4 = Node(genesis_creation_time=1,
                     node_id=4,
                     network=network,
                     block_signer=private_keys[4],
                     validators=validators,
                     behaviour=Behaviour())
        network.register_node(node4)

        node5 = Node(genesis_creation_time=1,
                     node_id=5,
                     network=network,
                     block_signer=private_keys[5],
                     validators=validators,
                     behaviour=Behaviour())
        network.register_node(node5)

        Time.advance_to_next_timeslot()  # current block number 1
        node0.step()  # create and sign block
        # validate block created and broadcasted
        # validate mempool is empty
        # validate tx by hash is empty
        self.list_validator(network.nodes, ['dag.blocks_by_number.length'], 2)
        self.list_validator(network.nodes, ['mempool.gossips.length'], 0)
        # validate 2 public key tx
        self.list_validator(network.nodes, ['dag.transactions_by_hash.length'], 1)

        # on one step sends +and- (add test for different steps ?)
        node1.step()  # ! maliciously sand positive and negative gossip (request by genesis 0 block)
        # all node receive positive gossip
        # txs for now only in mempool (not in block)
        self.list_validator(network.nodes, ['dag.blocks_by_number.length'], 2)
        # all nodes has 1-gossip and 6+gossips (1-gossip and 6+gossip from (0,1,2,3,4,5))
        self.list_validator(network.nodes, ['mempool.gossips.length'], 7)
        self.list_validator(network.nodes, ['dag.transactions_by_hash.length'], 1)

        node2.step()
        node3.step()
        node4.step()
        node5.step()
        # after all steps situation same
        self.list_validator(network.nodes, ['dag.blocks_by_number.length'], 2)
        self.list_validator(network.nodes, ['mempool.gossips.length'], 7)
        self.list_validator(network.nodes, ['dag.transactions_by_hash.length'], 1)

        Time.advance_to_next_timeslot()  # current block number 2
        node0.step()  # do nothing
        node1.step()  # is validator by order (need to marge mempool and provide block)
        # TODO in current case node will penaltize SELF !!!
        self.list_validator(network.nodes, ['dag.blocks_by_number.length'], 3)
        self.list_validator(network.nodes, ['mempool.gossips.length'], 0)
        # tx_s
        # 3 - public key tx
        # 1 - negative gossip tx
        # 6 - positive gossip txs
        # 1 - penalty tx
        # total = 11 txs
        self.list_validator(network.nodes, ['dag.transactions_by_hash.length'], 11)

        node2.step()
        node3.step()
        node4.step()
        node5.step()
        # validate that all keeps the same
        self.list_validator(network.nodes, ['dag.blocks_by_number.length'], 3)
        self.list_validator(network.nodes, ['mempool.gossips.length'], 0)
        self.list_validator(network.nodes, ['dag.transactions_by_hash.length'], 11)
        # verify that node1 is steel in validators list
        self.list_validator(network.nodes, ['permissions.epoch_validators.length'], 20)

        Time.advance_to_next_timeslot()  # current block number 3
        node0.step()  # do nothing
        node1.step()  # do nothing
        node2.step()  # provide block
        node3.step()
        node4.step()
        node5.step()

        # validate new block by node2
        self.list_validator(network.nodes, ['dag.blocks_by_number.length'], 4)
        # verify that node1 is steel in validators list until epoch end
        self.list_validator(network.nodes, ['permissions.epoch_validators.length'], 20)

        for i in range(5, 22):
            Time.advance_to_next_timeslot()
            if i == 21:
                node0.step()
            node0.step()
            node1.step()
            node2.step()
            node3.step()
            node4.step()
            node5.step()
            if i == 21:
                # ! chek up validators list on new epoch upcoming
                # TODO sometimes fall for unknoun reason
                self.list_validator(network.nodes, ['dag.blocks_by_number.length'], i-1)
                self.list_validator(network.nodes, ['permissions.epoch_validators.length'], 19)
                # TODO nodes recalculates 2 times ?
                self.list_validator(network.nodes, ['permissions.epoch_validators.epoch0.length'], 19)  # maybe 20?
                self.list_validator(network.nodes, ['permissions.epoch_validators.epoch1.length'], 19)
                # !
            else:
                self.list_validator(network.nodes, ['dag.blocks_by_number.length'], i)
                self.list_validator(network.nodes, ['permissions.epoch_validators.length'], 20)

    # -------------------------------------------------------------------
    # Internal
    # -------------------------------------------------------------------
    def list_validator(self, node_list, functions, value):
        """
            Method provide check of registered for network nodes (or custom nodes list to check)
            and perform assertTrue for all nodes in nodes_list for specific parameter by value
            :param node_list: list of nodes for validation
            :param functions: see list of params in method or add necessary
            :param value: value of condition
            :return: nothing (provide assertation)
        """
        for node in node_list:
            if 'mempool.gossips.length' in functions:
                self.assertEqual(len(node.mempool.gossips), value)
            if 'dag.blocks_by_number.length' in functions:
                self.assertEqual(len(node.dag.blocks_by_number), value)
            if 'dag.transactions_by_hash.length' in functions:
                self.assertEqual(len(node.dag.transactions_by_hash), value)
            if 'permissions.epoch_validators.length' in functions:
                validators_list = node.permissions.epoch_validators
                validators_list = next(iter(validators_list.values()))
                self.assertEqual(len(validators_list), value)
            if 'permissions.epoch_validators.epoch0.length' in functions:
                validators_list = node.permissions.epoch_validators
                validators_list = next(iter(validators_list.values()))
                self.assertEqual(len(validators_list), value)
            if 'permissions.epoch_validators.epoch1.length' in functions:
                validators_list = node.permissions.epoch_validators
                validators_list = next(iter(validators_list.values()))
                self.assertEqual(len(validators_list), value)

