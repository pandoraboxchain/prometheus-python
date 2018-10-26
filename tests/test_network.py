import unittest

from node.behaviour import Behaviour
from node.block_signers import BlockSigners
from node.network import Network
from node.validators import Validators
from tools.time import Time
from chain.epoch import Epoch
from node.node import Node
from visualization.dag_visualizer import DagVisualizer

from chain.params import ROUND_DURATION, BLOCK_TIME


class TestNodeAPI(unittest.TestCase):

    @unittest.skip('test ancessor for block')
    def test_network_methods(self):
        private_keys = BlockSigners()
        private_keys = private_keys.block_signers
        validators = Validators()

        network = Network()

        node0 = Node(genesis_creation_time=1,
                     node_id=0,
                     network=network,
                     block_signer=private_keys[0],
                     validators=validators,
                     behaviour=Behaviour())

        node1 = Node(genesis_creation_time=1,
                     node_id=1,
                     network=network,
                     block_signer=private_keys[1],
                     validators=validators,
                     behaviour=Behaviour())

        node2 = Node(genesis_creation_time=1,
                     node_id=2,
                     network=network,
                     block_signer=private_keys[2],
                     validators=validators,
                     behaviour=Behaviour())

        node3 = Node(genesis_creation_time=1,
                     node_id=3,
                     network=network,
                     block_signer=private_keys[3],
                     validators=validators,
                     behaviour=Behaviour())

        node4 = Node(genesis_creation_time=1,
                     node_id=4,
                     network=network,
                     block_signer=private_keys[4],
                     validators=validators,
                     behaviour=Behaviour())

        network.register_node(node0)
        network.register_node(node1)
        network.register_node(node2)
        network.register_node(node3)
        network.register_node(node4)

        self.assertEqual(len(network.nodes) == 5, True)

        network.move_nodes_to_group(0, [node0, node1])  # create group 0 with nodes 0, 1
        network.move_nodes_to_group(1, [node2, node3, node4])  # create group 1 with nodes 2, 3, 4

        self.assertEqual(len(network.groups) == 2, True)
        self.assertEqual(len(network.groups[0]) == 2, True)
        self.assertEqual(len(network.groups[1]) == 3, True)

        network.merge_all_groups()  # test marge groups
        self.assertEqual(len(network.nodes) == 5, True)

    @unittest.skip('test ancessor for block')
    def test_node_broadcast_unavailable(self):
        Time.use_test_time()
        Time.set_current_time(1)

        private_keys = BlockSigners()
        private_keys = private_keys.block_signers

        validators = Validators()
        validators.validators = Validators.read_genesis_validators_from_file()
        validators.signers_order = [0] + [1] * Epoch.get_duration()
        validators.randomizers_order = [0] * Epoch.get_duration()

        network = Network()

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

    @unittest.skip('test ancessor for block')
    def test_node_handle_unavailable(self):
        Time.use_test_time()
        Time.set_current_time(1)

        private_keys = BlockSigners()
        private_keys = private_keys.block_signers

        validators = Validators()
        validators.validators = Validators.read_genesis_validators_from_file()
        validators.signers_order = [0] + [1] * Epoch.get_duration()
        validators.randomizers_order = [0] * Epoch.get_duration()

        network = Network()

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
        DagVisualizer.visualize(node0.dag)

    @unittest.skip('test ancessor for block')
    def test_node_offline(self):
        Time.use_test_time()
        Time.set_current_time(1)

        private_keys = BlockSigners()
        private_keys = private_keys.block_signers

        validators = Validators()
        validators.validators = Validators.read_genesis_validators_from_file()
        validators.signers_order = [0] + [1] + [2] * Epoch.get_duration()
        validators.randomizers_order = [0] * Epoch.get_duration()

        network = Network()

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

    @unittest.skip('test two chains groups')
    def test_make_node_offline_from_block(self):
        Time.use_test_time()
        Time.set_current_time(1)

        private_keys = BlockSigners()
        private_keys = private_keys.block_signers

        validators = Validators()
        validators.validators = Validators.read_genesis_validators_from_file()
        validators.signers_order = [0] + [1] + [2] * Epoch.get_duration()
        validators.randomizers_order = [0] * Epoch.get_duration()

        network = Network()

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
        node2.step()  # DO NOT RECEIVE BLOCK wait for nex step # + produce but not broadcast negative gossip
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

        # ------------------------------- block 7 (timeslot)
        # node 2 make online again on step
        Time.advance_to_next_timeslot()
        node0.step()  # provide negative gossip for block 6 before creating and broadcasting block
        node1.step()  # provide negative gossip for block 6
        node2.step()  # current step makes node online (its do not receive gossips from node0 and node1) (variant A)

        self.assertEqual(len(node0.dag.blocks_by_number), 6)
        self.assertEqual(len(node1.dag.blocks_by_number), 6)
        self.assertEqual(len(node2.dag.blocks_by_number), 6)

        # visualization and description block ===========================================
        # DagVisualizer.visualize(node0.dag)
        # DagVisualizer.visualize(node2.dag)
        # on current time nodes have such blocks
        # timeslot[0, 1, 2, 3, 4, 5, 6,     7]
        # ====================================
        # node0 - [0, 1, 2, 3, 4, 5, <>, node0]
        # node1 - [0, 1, 2, 3, 4, 5, <>,      ]
        # node2 - [0, 1, 2, 3, 4, <>, 6,      ]

        # ancessor for block 7 is block 5
        # ancessor for block 5 is block 4

        # node2 request block 5 as ancestor for block 7 (block 6 was skipped till node was offline)
        # node2 received and insert block 5 as conflict to empty timeslot till offline to block 6
        # block 6 was created offline, need to skip all its tx's and softly drop
        # visualization and description block ===========================================

        # node0 - provide block 7
        node0.step()  # create and broadcast block number 7

        # visualization and description block ===========================================
        # DagVisualizer.visualize(node0.dag)  # [0,1,2,3,4,5,6,<>,7]
        # by timeslots                          [           5,<>, 6]
        # DagVisualizer.visualize(node2.dag)  # [0,1,2,3,4,<>, 6, -]
        # visualization and description block ===========================================

        node1.step()  # handle and add block normaly
        node2.step()  # handled all ancestor blocks and inset it to dag with processing included transactions

        self.assertEqual(len(node0.dag.blocks_by_number), 7)
        self.assertEqual(len(node1.dag.blocks_by_number), 7)
        self.assertEqual(len(node2.dag.blocks_by_number), 8)  # steel have redundant block 6

        # ------------------------------- block 8 (timeslot)
        # all nodes online
        Time.advance_to_next_timeslot()
        node0.step()
        node1.step()
        node2.step()

        self.assertEqual(len(node0.dag.blocks_by_number), 8)
        self.assertEqual(len(node1.dag.blocks_by_number), 8)
        self.assertEqual(len(node2.dag.blocks_by_number), 9)  # steel have redundant block 6

    def test_two_network_groups(self):
        Time.use_test_time()
        Time.set_current_time(1)

        private_keys = BlockSigners()
        private_keys = private_keys.block_signers

        validators = Validators()
        validators.validators = Validators.read_genesis_validators_from_file()
        validators.signers_order = ([0, 1, 2, 3, 4, 5, 6] * Epoch.get_duration()) * 2
        validators.randomizers_order = ([0] * Epoch.get_duration()) * 2

        network = Network()

        node0 = Node(genesis_creation_time=1,
                     node_id=0,
                     network=network,
                     block_signer=private_keys[0],
                     validators=validators,
                     behaviour=Behaviour())
        node1 = Node(genesis_creation_time=1,
                     node_id=1,
                     network=network,
                     block_signer=private_keys[1],
                     validators=validators,
                     behaviour=Behaviour())
        node2 = Node(genesis_creation_time=1,
                     node_id=2,
                     network=network,
                     block_signer=private_keys[2],
                     validators=validators,
                     behaviour=Behaviour())
        node3 = Node(genesis_creation_time=1,
                     node_id=3,
                     network=network,
                     block_signer=private_keys[3],
                     validators=validators,
                     behaviour=Behaviour())
        node4 = Node(genesis_creation_time=1,
                     node_id=4,
                     network=network,
                     block_signer=private_keys[4],
                     validators=validators,
                     behaviour=Behaviour())
        node5 = Node(genesis_creation_time=1,
                     node_id=5,
                     network=network,
                     block_signer=private_keys[5],
                     validators=validators,
                     behaviour=Behaviour())
        node6 = Node(genesis_creation_time=1,
                     node_id=6,
                     network=network,
                     block_signer=private_keys[6],
                     validators=validators,
                     behaviour=Behaviour())

        # all in one network
        network.register_node(node0)
        network.register_node(node1)
        network.register_node(node2)
        network.register_node(node3)
        network.register_node(node4)
        network.register_node(node5)
        network.register_node(node6)
        self.assertEqual(len(network.nodes) == 7, True)

        # move some timeslots for blocks generate
        last_block_range = 0
        for i in range(0, ROUND_DURATION * 6 + 2):  # for epoch (max i == 19 on 3 round duration)
            Time.advance_to_next_timeslot()
            for s in range(0, BLOCK_TIME):  # steps per timeslot
                node0.step()
                node1.step()
                node2.step()
                node3.step()
                node4.step()
                node5.step()
                node6.step()
            last_block_range = i

        # validate new epoch
        DagVisualizer.visualize(node0.dag)
        DagVisualizer.visualize(node6.dag)

        for i in range(last_block_range, last_block_range+10):  # move to epoch/2 block
            Time.advance_to_next_timeslot()
            for s in range(0, BLOCK_TIME):  # steps per timeslot
                node0.step()
                node1.step()
                node2.step()
                node3.step()
                node4.step()
                node5.step()
                node6.step()
            last_block_range = i

        DagVisualizer.visualize(node0.dag)  # TODO strange! blocks behaviour
        DagVisualizer.visualize(node6.dag)