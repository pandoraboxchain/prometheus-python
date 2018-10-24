import unittest

from node.behaviour import Behaviour
from node.block_signers import BlockSigners
from node.node_api import NodeApi
from node.validators import Validators
from tools.time import Time
from chain.epoch import Epoch
from node.node import Node
from visualization.dag_visualizer import DagVisualizer


class TestNodeAPI(unittest.TestCase):

    def test_node_broadcast_unavailable(self):
        Time.use_test_time()
        Time.set_current_time(1)

        private_keys = BlockSigners()
        private_keys = private_keys.block_signers

        validators = Validators()
        validators.validators = Validators.read_genesis_validators_from_file()
        validators.signers_order = [0] + [1] * Epoch.get_duration()
        validators.randomizers_order = [0] * Epoch.get_duration()

        network = NodeApi()

        node0 = Node(genesis_creation_time=1,
                     node_id=0,
                     network=network,
                     block_signer=private_keys[0],
                     validators=validators,
                     behaviour=Behaviour())
        network.register_node(node0)

        # behaviour flag for disabling node to broadcast
        behaviour = Behaviour()
        behaviour.transport_node_disable_output = True
        node1 = Node(genesis_creation_time=1,
                     node_id=1,
                     network=network,
                     block_signer=private_keys[1],
                     validators=validators,
                     behaviour=behaviour)
        network.register_node(node1)

        Time.advance_to_next_timeslot()
        node0.step()  # provide block
        self.assertEqual(len(node0.dag.blocks_by_number), 2)  # ensure that node0 provide block to chain
        self.assertEqual(len(node1.dag.blocks_by_number), 2)  # ensure that node1 receive block

        node1.step()  # do nothing
        self.assertEqual(len(node0.dag.blocks_by_number), 2)
        self.assertEqual(len(node1.dag.blocks_by_number), 2)

        Time.advance_to_next_timeslot()
        node0.step()  # do nothing
        node1.step()  # node1 must provide block (and public key tx) but unable to broadcast it by network
        self.assertEqual(len(node0.dag.blocks_by_number), 2)
        self.assertEqual(len(node1.dag.blocks_by_number), 3)

    def test_node_handle_unavailable(self):
        Time.use_test_time()
        Time.set_current_time(1)

        private_keys = BlockSigners()
        private_keys = private_keys.block_signers

        validators = Validators()
        validators.validators = Validators.read_genesis_validators_from_file()
        validators.signers_order = [0] + [1] * Epoch.get_duration()
        validators.randomizers_order = [0] * Epoch.get_duration()

        network = NodeApi()

        node0 = Node(genesis_creation_time=1,
                     node_id=0,
                     network=network,
                     block_signer=private_keys[0],
                     validators=validators,
                     behaviour=Behaviour())

        network.register_node(node0)

        # behaviour flag for disabling node to broadcast
        behaviour = Behaviour()
        behaviour.transport_node_disable_input = True
        node1 = Node(genesis_creation_time=1,
                     node_id=1,
                     network=network,
                     block_signer=private_keys[1],
                     validators=validators,
                     behaviour=behaviour)
        network.register_node(node1)

        Time.advance_to_next_timeslot()
        node0.step()  # provide block
        self.assertEqual(len(node0.dag.blocks_by_number), 2)  # ensure that node0 provide block to chain
        self.assertEqual(len(node1.dag.blocks_by_number), 1)  # ensure that node1 DO NOT receive block
        node1.step()

        Time.advance_to_next_timeslot()
        node0.step()  # do nothing
        node1.step()  # send negative gossip (block from node0 not received)

        self.assertEqual(len(node0.mempool.gossips), 2)  # ensure negative gossip received by node0 (+positive gossip)
        self.assertEqual(len(node1.mempool.gossips), 1)  # ensure node1 NOT receive positive gossip

        node0.step()  # provide and block by hash in gossip logic scope
        node1.step()  # node1 do not ask block by hash (cant receive positive gossip due behaviour)
        # for node1 block 1 (created by node 0) is not available due behaviour
        # node1 produce block by step and sand it by broadcast

        self.assertEqual(len(node0.dag.blocks_by_number), 3)  # NODE_0 have 2 blocks with genesis ancestor
        self.assertEqual(len(node1.dag.blocks_by_number), 2)  # have genesis + self produced block

        # uncomment for visual ensure that on NODE_0 have 2 blocks with genesis ancestor
        # DagVisualizer.visualize(node0.dag)

    def test_node_offline(self):
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

        node1 = Node(genesis_creation_time=1,
                     node_id=1,
                     network=network,
                     block_signer=private_keys[1],
                     validators=validators,
                     behaviour=Behaviour())
        network.register_node(node1)

        behaviour = Behaviour()
        behaviour.transport_node_disable_input = True
        behaviour.transport_node_disable_output = True
        node2 = Node(genesis_creation_time=1,
                     node_id=2,
                     network=network,
                     block_signer=private_keys[2],
                     validators=validators,
                     behaviour=behaviour)
        network.register_node(node2)  # emulate node total offline

        Time.advance_to_next_timeslot()
        node0.step()  # provide block
        node1.step()
        node2.step()

        self.assertEqual(len(node0.dag.blocks_by_number), 2)
        self.assertEqual(len(node1.dag.blocks_by_number), 2)
        self.assertEqual(len(node2.dag.blocks_by_number), 1)  # steel have 1 block

        Time.advance_to_next_timeslot()
        node0.step()
        node1.step()  # provide block
        node2.step()

        self.assertEqual(len(node0.dag.blocks_by_number), 3)
        self.assertEqual(len(node1.dag.blocks_by_number), 3)
        self.assertEqual(len(node2.dag.blocks_by_number), 1)  # steel have 1 block

        Time.advance_to_next_timeslot()
        node0.step()
        node1.step()
        node2.step()  # wit for block and try to broadcast negative gossip

        self.assertEqual(len(node0.dag.blocks_by_number), 3)
        self.assertEqual(len(node1.dag.blocks_by_number), 3)
        self.assertEqual(len(node2.dag.blocks_by_number), 1)

        node0.step()
        node1.step()
        node2.step()  # provide block BUT DO NOT BROADCAST

        self.assertEqual(len(node0.dag.blocks_by_number), 3)
        self.assertEqual(len(node1.dag.blocks_by_number), 3)
        self.assertEqual(len(node2.dag.blocks_by_number), 2)

    @unittest.skip('INTERESTING CASE')
    def test_make_node_offline_from_block(self):
        Time.use_test_time()
        Time.set_current_time(1)

        private_keys = BlockSigners()
        private_keys = private_keys.block_signers

        validators = Validators()
        validators.validators = Validators.read_genesis_validators_from_file()
        validators.signers_order = [0] + [1] + [2] + [0] + [1] + [2] + [0] + [1] + [2] * Epoch.get_duration()
        validators.randomizers_order = [0] * Epoch.get_duration()

        network = NodeApi()

        node0 = Node(genesis_creation_time=1,
                     node_id=0,
                     network=network,
                     block_signer=private_keys[0],
                     validators=validators,
                     behaviour=Behaviour())
        network.register_node(node0)

        node1 = Node(genesis_creation_time=1,
                     node_id=1,
                     network=network,
                     block_signer=private_keys[1],
                     validators=validators,
                     behaviour=Behaviour())
        network.register_node(node1)

        behaviour = Behaviour()
        behaviour.transport_keep_offline = [4, 6]  # keep offline from 4 block till 6 block
        node2 = Node(genesis_creation_time=1,
                     node_id=2,
                     network=network,
                     block_signer=private_keys[2],
                     validators=validators,
                     behaviour=behaviour)
        network.register_node(node2)  # emulate node total offline from 4 block till 6 block

        # ------------------------------- block 1
        Time.advance_to_next_timeslot()
        node0.step()  # provide block
        node1.step()
        node2.step()
        self.assertEqual(len(node0.dag.blocks_by_number), 2)
        self.assertEqual(len(node1.dag.blocks_by_number), 2)
        self.assertEqual(len(node2.dag.blocks_by_number), 2)

        # ------------------------------- block 2
        Time.advance_to_next_timeslot()
        node0.step()
        node1.step()  # provide block
        node2.step()
        self.assertEqual(len(node0.dag.blocks_by_number), 3)
        self.assertEqual(len(node1.dag.blocks_by_number), 3)
        self.assertEqual(len(node2.dag.blocks_by_number), 3)

        # ------------------------------- block 3
        Time.advance_to_next_timeslot()
        node0.step()
        node1.step()
        node2.step()  # provide block
        self.assertEqual(len(node0.dag.blocks_by_number), 4)
        self.assertEqual(len(node1.dag.blocks_by_number), 4)
        self.assertEqual(len(node2.dag.blocks_by_number), 4)

        # ------------------------------- block 4
        # node 2 must set offline on next block
        Time.advance_to_next_timeslot()
        node0.step()  # provide block
        node1.step()
        node2.step()  # AFTER NODE STEP IT MAKES OFFLINE !
        self.assertEqual(len(node0.dag.blocks_by_number), 5)
        self.assertEqual(len(node1.dag.blocks_by_number), 5)
        self.assertEqual(len(node2.dag.blocks_by_number), 5)  # RECEIVE BLOCK BEFORE BEHAVIOUR UPDATES

        # ------------------------------- block 5
        # node 2 offline
        Time.advance_to_next_timeslot()
        node0.step()
        node1.step()  # provide block
        node2.step()
        self.assertEqual(len(node0.dag.blocks_by_number), 6)
        self.assertEqual(len(node1.dag.blocks_by_number), 6)
        self.assertEqual(len(node2.dag.blocks_by_number), 5)  # DO NOT RECEIVE BLOCK !

        # ------------------------------- block 6
        # node 2 offline
        Time.advance_to_next_timeslot()
        node0.step()
        node1.step()
        node2.step()  # DO NOT RECEIVE BLOCK wait for nex step
        self.assertEqual(len(node0.dag.blocks_by_number), 6)
        self.assertEqual(len(node1.dag.blocks_by_number), 6)
        self.assertEqual(len(node2.dag.blocks_by_number), 5)  # DO NOT RECEIVE BLOCK !

        node0.step()
        node1.step()
        # node 2 try to sand negative gossip by block 5 (on offline store it in local mempool and add to block !!!!!!!)
        # NODE_0 AND NODE_1 DO NOT RECEIVE NEGATIVE GOSSIP BY BLOCK 5
        node2.step()  # create and store block localy (steel offline)
        self.assertEqual(len(node0.dag.blocks_by_number), 6)
        self.assertEqual(len(node1.dag.blocks_by_number), 6)
        self.assertEqual(len(node2.dag.blocks_by_number), 6)  # node 2 forks chain

        # ------------------------------- block 7
        # node 2 make online again on step
        Time.advance_to_next_timeslot()
        node2.step()  # current step makes node online (available for gossip listening) (variant B)

        # TODO if NODE_2 step BEFORE NODE_0, node_0 will CRASH on trying to delete negative gossip from local mempool by block 5 vhich not exist! (variant B)
        node0.step()  # provide negative gossip for block 6 before creating and broadcasting block
        node1.step()  # provide negative gossip for block 6

        # node2.step()  # current step makes node online (its do not receive gossips from node0 and node1) (variant A)

        self.assertEqual(len(node0.dag.blocks_by_number), 6)
        self.assertEqual(len(node1.dag.blocks_by_number), 6)
        self.assertEqual(len(node2.dag.blocks_by_number), 6)

        node0.step()  # create and broadcast block number 7
        node1.step()  # handle and add block normaly
        node2.step()  # TODO crash on block handle! (in case validator make offline on term signing and broadcasting) (variant A)

    @unittest.skip('GROUP INTERESTING CASE')
    def test_network_groups(self):
        Time.use_test_time()
        Time.set_current_time(1)

        private_keys = BlockSigners()
        private_keys = private_keys.block_signers

        validators = Validators()
        validators.validators = Validators.read_genesis_validators_from_file()
        validators.signers_order = [0] + [1] + [2] + [0] + [1] + [2] + [0] + [1] + [2] * Epoch.get_duration()
        validators.randomizers_order = [0] * Epoch.get_duration()

        network = NodeApi(0, 1)

        # node 0 exist in network0
        node0 = Node(genesis_creation_time=1,
                     node_id=0,
                     network=network,
                     block_signer=private_keys[0],
                     validators=validators,
                     behaviour=Behaviour())
        network.register_node(node0, 0)

        # node 1 exist in network0 and network1
        node1 = Node(genesis_creation_time=1,
                     node_id=1,
                     network=network,
                     block_signer=private_keys[1],
                     validators=validators,
                     behaviour=Behaviour())
        network.register_node(node1, 0, 1)

        # node 2 exist in network1
        node2 = Node(genesis_creation_time=1,
                     node_id=2,
                     network=network,
                     block_signer=private_keys[2],
                     validators=validators,
                     behaviour=Behaviour())
        network.register_node(node2, 1)

        # assert nodes groups
        self.assertTrue(network.groups is not None)
        self.assertEqual(len(network.groups[0]) == 2, True)
        self.assertEqual(len(network.groups[1]) == 2, True)

        # ------------------------------- block 1
        Time.advance_to_next_timeslot()
        node0.step()  # provide block
        node1.step()  # node1 in group0 receive block
        node2.step()  # node2 do not receive block (its in group1)

        self.assertEqual(len(node0.dag.blocks_by_number), 2)
        self.assertEqual(len(node1.dag.blocks_by_number), 2)
        self.assertEqual(len(node2.dag.blocks_by_number), 1)  # steel wait for block (node 2 is in another group)

        Time.advance_to_next_timeslot()
        node0.step()
        node1.step()  # provide block to network group1 and group2
        node2.step()

        # TODO after node1 provide block node 2 crashes when try to delete not existed public key tx on node2 handle


