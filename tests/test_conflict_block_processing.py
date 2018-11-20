import unittest
import logging

from node.behaviour import Behaviour
from chain.block_factory import BlockFactory
from chain.epoch import Epoch
from node.block_signers import BlockSigners, BlockSigner
from node.node import Node
from node.network import Network
from node.validators import Validators
from crypto.private import Private
from tools.time import Time

from chain.params import Round, ROUND_DURATION
from visualization.dag_visualizer import DagVisualizer


# TODO test for transaction and block count base logic            : Done
# TODO test 2,3,4 blocks                                          : Done
# TODO tets 2,3,4 blocks and + some 'out of network' nodes group  : resolves by orphan system
# TODO test for two malicious validator one by one
# TODO tets for epoch by epoch block
# TODO test for three malicious validators one by one %


class TestConflictBlockProcessing(unittest.TestCase):

    def test_conflict_block_validator_processing(self):
        Time.use_test_time()
        Time.set_current_time(1)

        private_keys = BlockSigners()
        private_keys = private_keys.block_signers

        validators = Validators()
        validators.validators = Validators.read_genesis_validators_from_file()

        network = Network()
        self.generate_nodes(network, private_keys, 19)  # create validators

        # generate blocks to new epoch
        self.perform_block_steps(network, 5)

        epoch_0_signers_order = list(network.nodes[0].permissions.signers_indexes.values())[0]  # SECOND! EPOCH
        next_malicious_signer_node_index = epoch_0_signers_order[5] # block count
        # set behavior for next validator is_malicious_excessive_block = True
        network.nodes[next_malicious_signer_node_index].behaviour.malicious_excessive_block_count = 1
        # perform next one block step
        self.perform_block_steps(network, 1)
        # nodes MUST HAVE 2 conflict blocks
        self.list_validator(network.nodes, ['dag.blocks_by_number.length'], 7)  # + 1 conflict
        network.nodes[next_malicious_signer_node_index].behaviour.malicious_excessive_block = False
        # -- next validator MUST get two block conflicts send transaction
        self.perform_block_steps(network, 1)
        # check all nodes block conflict transaction mined
        self.list_validator(network.nodes, ['dag.blocks_by_number.system_txs'], 1)
        # all nodes have all blocks test done
        self.list_validator(network.nodes, ['dag.blocks_by_number.length'], 8)

    def test_more_conflict_blocks(self):
        Time.use_test_time()
        Time.set_current_time(1)

        private_keys = BlockSigners()
        private_keys = private_keys.block_signers

        validators = Validators()
        validators.validators = Validators.read_genesis_validators_from_file()

        network = Network()
        self.generate_nodes(network, private_keys, 19)  # create validators

        # generate blocks to new epoch
        self.perform_block_steps(network, 5)

        epoch_0_signers_order = list(network.nodes[0].permissions.signers_indexes.values())[0]  # SECOND! EPOCH
        next_malicious_signer_node_index = epoch_0_signers_order[5]  # block count
        # set behavior for next validator is_malicious_excessive_block = True
        network.nodes[next_malicious_signer_node_index].behaviour.malicious_excessive_block_count = 2
        network.nodes[next_malicious_signer_node_index].tried_to_sign_current_block = False
        network.nodes[next_malicious_signer_node_index].last_signed_block_number = 0
        self.perform_block_steps(network, 1)
        #
        network.nodes[next_malicious_signer_node_index].tried_to_sign_current_block = False
        network.nodes[next_malicious_signer_node_index].last_signed_block_number = 0
        self.perform_block_steps(network, 1)
        #
        # nodes MUST HAVE +2 conflict blocks
        self.perform_block_steps(network, 1)
        self.perform_block_steps(network, 1)
        DagVisualizer.visualize(network.nodes[0].dag)
        self.list_validator(network.nodes, ['dag.blocks_by_number.length'], 10)  # + 2 conflict

        # -- next validator MUST get two block conflicts send transaction
        self.perform_block_steps(network, 1)
        # check all nodes block conflict transaction mined
        self.list_validator(network.nodes, ['dag.blocks_by_number.system_txs'], 1)
        # all nodes have all blocks test done
        self.list_validator(network.nodes, ['dag.blocks_by_number.length'], 11)

    def test_block_getter_by_node_groups(self):
        Time.use_test_time()
        Time.set_current_time(1)

        private_keys = BlockSigners()
        private_keys = private_keys.block_signers

        validators = Validators()
        validators.validators = Validators.read_genesis_validators_from_file()

        network = Network()
        self.generate_nodes(network, private_keys, 19)  # create validators
        # add validators for group
        self.add_stakeholders(network, 9)  # add stakeholders to network

        # generate blocks to new epoch
        self.perform_block_steps(network, 22)

        # divide network into two groups
        network.move_nodes_to_group_by_id(1, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19])
        network.move_nodes_to_group_by_id(2, [20, 21, 22, 23, 24, 25, 26, 27])

        # perform step for generate merged block
        epoch_0_signers_order = list(network.nodes[0].permissions.signers_indexes.values())[0]  # SECOND! EPOCH
        next_malicious_signer_node_index = epoch_0_signers_order[3]
        network.groups[1][next_malicious_signer_node_index].behaviour.malicious_excessive_block_count = 1

        self.perform_block_steps(network, 1)

        self.assertEqual(len(network.groups.get(1)[0].dag.blocks_by_hash), 25)  # group_1 = 25 blocks
        self.assertEqual(len(network.groups.get(2)[0].dag.blocks_by_hash), 23)  # group_2 = 23 blocks
        # DagVisualizer.visualize(network.groups.get(1)[0].dag)
        # DagVisualizer.visualize(network.groups.get(2)[0].dag)

        network.merge_all_groups()

        self.assertEqual(len(network.nodes[0].dag.blocks_by_hash), 25)
        self.assertEqual(len(network.nodes[27].dag.blocks_by_hash), 23)

        self.perform_block_steps(network, 1)

        # TODO all blocks are received and marged by orphan system
        self.assertEqual(len(network.nodes[0].dag.blocks_by_hash), 26)
        self.assertEqual(len(network.nodes[27].dag.blocks_by_hash), 26)
        # DagVisualizer.visualize(network.nodes[0].dag)
        # DagVisualizer.visualize(network.nodes[27].dag)
    # -------------------------------------------------------------------
    # Internal
    # -------------------------------------------------------------------
    @staticmethod
    def generate_nodes(network, block_signers, count):
        behaviour = Behaviour()
        for i in range(0, count):
            logger = logging.getLogger("Node " + str(i))
            node = Node(genesis_creation_time=1,
                        node_id=i,
                        network=network,
                        behaviour=behaviour,
                        block_signer=block_signers[i],
                        logger=logger)
            network.register_node(node)

    @staticmethod
    def add_stakeholders(network, count):
        behaviour = Behaviour()
        behaviour.wants_to_hold_stake = True
        for i in range(0, count):
            index = len(network.nodes)
            logger = logging.getLogger("Node " + str(index))
            node = Node(genesis_creation_time=1,
                        block_signer=BlockSigner(Private.generate()),
                        node_id=index,
                        network=network,
                        behaviour=behaviour,
                        logger=logger)
            network.register_node(node)

    @staticmethod
    def perform_block_steps(network, timeslote_count):
        for t in range(0, timeslote_count):  # by timeslots
            Time.advance_to_next_timeslot()
            for s in range(0, ROUND_DURATION):  # by steps
                for node in network.nodes:  # by nodes
                    node.step()

    @staticmethod
    def perform_in_block_single_step(network, count):
        for s in range(0, count):
            for node in network.nodes:  # by nodes
                node.step()

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
            if 'dag.blocks_by_number.system_txs' in functions:
                conflict_tx_block = node.dag.blocks_by_number[7]
                self.assertEqual(len(conflict_tx_block[0].block.system_txs), value)

