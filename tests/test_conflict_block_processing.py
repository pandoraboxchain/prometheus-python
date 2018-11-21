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
from tests.test_helper import TestHelper
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
        helper = TestHelper(network)
        helper.generate_nodes(private_keys, 19)  # create validators

        # generate blocks to new epoch
        helper.perform_block_steps(5)

        epoch_0_signers_order = list(network.nodes[0].permissions.signers_indexes.values())[0]  # SECOND! EPOCH
        next_malicious_signer_node_index = epoch_0_signers_order[5] # block count
        # set behavior for next validator is_malicious_excessive_block = True
        network.nodes[next_malicious_signer_node_index].behaviour.malicious_excessive_block_count = 1
        # perform next one block step
        helper.perform_block_steps(1)
        # nodes MUST HAVE 2 conflict blocks
        helper.list_validator(network.nodes, ['dag.blocks_by_number.length'], 7)  # + 1 conflict
        network.nodes[next_malicious_signer_node_index].behaviour.malicious_excessive_block = False
        # -- next validator MUST get two block conflicts send transaction
        helper.perform_block_steps(1)
        # check all nodes block conflict transaction mined
        helper.list_validator(network.nodes, ['dag.blocks_by_number.system_txs'], 1)
        # all nodes have all blocks test done
        helper.list_validator(network.nodes, ['dag.blocks_by_number.length'], 8)

    def test_more_conflict_blocks(self):
        Time.use_test_time()
        Time.set_current_time(1)

        private_keys = BlockSigners()
        private_keys = private_keys.block_signers

        validators = Validators()
        validators.validators = Validators.read_genesis_validators_from_file()

        network = Network()
        helper = TestHelper(network)
        helper.generate_nodes(private_keys, 19)  # create validators

        # generate blocks to new epoch
        helper.perform_block_steps(5)

        epoch_0_signers_order = list(network.nodes[0].permissions.signers_indexes.values())[0]  # SECOND! EPOCH
        next_malicious_signer_node_index = epoch_0_signers_order[5]  # block count
        # set behavior for next validator is_malicious_excessive_block = True
        network.nodes[next_malicious_signer_node_index].behaviour.malicious_excessive_block_count = 2
        network.nodes[next_malicious_signer_node_index].tried_to_sign_current_block = False
        network.nodes[next_malicious_signer_node_index].last_signed_block_number = 0
        helper.perform_block_steps(1)
        #
        network.nodes[next_malicious_signer_node_index].tried_to_sign_current_block = False
        network.nodes[next_malicious_signer_node_index].last_signed_block_number = 0
        helper.perform_block_steps(1)
        #
        # nodes MUST HAVE +2 conflict blocks
        helper.perform_block_steps(1)
        helper.perform_block_steps(1)
        DagVisualizer.visualize(network.nodes[0].dag)
        helper.list_validator(network.nodes, ['dag.blocks_by_number.length'], 10)  # + 2 conflict

        # -- next validator MUST get two block conflicts send transaction
        helper.perform_block_steps(1)
        # check all nodes block conflict transaction mined
        helper.list_validator(network.nodes, ['dag.blocks_by_number.system_txs'], 1)
        # all nodes have all blocks test done
        helper.list_validator(network.nodes, ['dag.blocks_by_number.length'], 11)

    def test_block_getter_by_node_groups(self):
        Time.use_test_time()
        Time.set_current_time(1)

        private_keys = BlockSigners()
        private_keys = private_keys.block_signers

        validators = Validators()
        validators.validators = Validators.read_genesis_validators_from_file()

        network = Network()
        helper = TestHelper(network)
        helper.generate_nodes(private_keys, 19)  # create validators
        # add validators for group
        helper.add_stakeholders(9)  # add stakeholders to network

        # generate blocks to new epoch
        helper.perform_block_steps(22)

        # divide network into two groups
        network.move_nodes_to_group_by_id(1, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19])
        network.move_nodes_to_group_by_id(2, [20, 21, 22, 23, 24, 25, 26, 27])

        # perform step for generate merged block
        epoch_0_signers_order = list(network.nodes[0].permissions.signers_indexes.values())[0]  # SECOND! EPOCH
        next_malicious_signer_node_index = epoch_0_signers_order[3]
        network.groups[1][next_malicious_signer_node_index].behaviour.malicious_excessive_block_count = 1

        helper.perform_block_steps(1)

        self.assertEqual(len(network.groups.get(1)[0].dag.blocks_by_hash), 25)  # group_1 = 25 blocks
        self.assertEqual(len(network.groups.get(2)[0].dag.blocks_by_hash), 23)  # group_2 = 23 blocks
        # DagVisualizer.visualize(network.groups.get(1)[0].dag)
        # DagVisualizer.visualize(network.groups.get(2)[0].dag)

        network.merge_all_groups()

        self.assertEqual(len(network.nodes[0].dag.blocks_by_hash), 25)
        self.assertEqual(len(network.nodes[27].dag.blocks_by_hash), 23)

        helper.perform_block_steps(1)

        # TODO all blocks are received and marged by orphan system
        self.assertEqual(len(network.nodes[0].dag.blocks_by_hash), 26)
        self.assertEqual(len(network.nodes[27].dag.blocks_by_hash), 26)
        # DagVisualizer.visualize(network.nodes[0].dag)
        # DagVisualizer.visualize(network.nodes[27].dag)
