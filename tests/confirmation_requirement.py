import unittest

from chain.dag import Dag
from chain.block_factory import BlockFactory
from chain.confirmation_requirement import ConfirmationRequirement
from crypto.private import Private
from visualization.dag_visualizer import DagVisualizer
from tests.test_chain_generator import TestChainGenerator


class TestConfirmationRequirement(unittest.TestCase):

    def test_recursive_sequence_found(self):
        dag = Dag(0)
        conf_req = ConfirmationRequirement(dag)

        genesis_hash = dag.genesis_block().get_hash()

        block_hash = TestChainGenerator.insert_dummy(dag, [genesis_hash], 1)
        conf_req.blocks[block_hash] = 2
        block_hash = TestChainGenerator.insert_dummy(dag, [genesis_hash], 1)
        conf_req.blocks[block_hash] = 3

        block_hash = TestChainGenerator.insert_dummy(dag, dag.get_top_hashes(), 2)
        conf_req.blocks[block_hash] = 3

        last_block_in_seq_hash = TestChainGenerator.insert_dummy(dag, [genesis_hash], 1)
        conf_req.blocks[last_block_in_seq_hash] = 3
        block_hash = TestChainGenerator.insert_dummy(dag, [genesis_hash], 1)
        conf_req.blocks[block_hash] = 3

        block_hash = TestChainGenerator.insert_dummy(dag, [last_block_in_seq_hash, block_hash], 2)
        conf_req.blocks[block_hash] = 4

        block_hash = TestChainGenerator.insert_dummy(dag, dag.get_top_hashes(), 3)
        conf_req.blocks[block_hash] = 4

        block_hash = TestChainGenerator.insert_dummy(dag, dag.get_top_hashes(), 4)

        # DagVisualizer.visualize(dag, True) # take a look to understand what's going on

        # there will be only two blocks with consecutive 4 behind, which is not enough to increase
        best_requirement = conf_req.choose_next_best_requirement(block_hash)
        self.assertEqual(best_requirement, 4)

        # make three blocks with consecutive 4 behind
        # it should lead to following block increasing requirement value
        conf_req.blocks[last_block_in_seq_hash] = 4
        best_requirement = conf_req.choose_next_best_requirement(block_hash)
        self.assertEqual(best_requirement, 5)