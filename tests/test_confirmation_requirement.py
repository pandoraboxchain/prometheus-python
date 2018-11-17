import unittest

from chain.block_factory import BlockFactory
from chain.confirmation_requirement import ConfirmationRequirement
from chain.dag import Dag
from chain.skipped_block import SkippedBlock
from chain.params import ZETA_MAX
from crypto.private import Private
from tools.chain_generator import ChainGenerator
from visualization.dag_visualizer import DagVisualizer


class TestConfirmationRequirement(unittest.TestCase):

    def test_recursive_sequence_found(self):
        dag = Dag(0)
        conf_req = ConfirmationRequirement(dag)

        genesis_hash = dag.genesis_block().get_hash()

        block_hash = ChainGenerator.insert_dummy(dag, [genesis_hash], 1)
        conf_req.blocks[block_hash] = 2
        block_hash = ChainGenerator.insert_dummy(dag, [genesis_hash], 1)
        conf_req.blocks[block_hash] = 3

        block_hash = ChainGenerator.insert_dummy(dag, dag.get_top_hashes(), 2)
        conf_req.blocks[block_hash] = 3

        last_block_in_seq_hash = ChainGenerator.insert_dummy(dag, [genesis_hash], 1)
        conf_req.blocks[last_block_in_seq_hash] = 3
        block_hash = ChainGenerator.insert_dummy(dag, [genesis_hash], 1)
        conf_req.blocks[block_hash] = 3

        block_hash = ChainGenerator.insert_dummy(dag, [last_block_in_seq_hash, block_hash], 2)
        conf_req.blocks[block_hash] = 4

        block_hash = ChainGenerator.insert_dummy(dag, dag.get_top_hashes(), 3)
        conf_req.blocks[block_hash] = 4

        block_hash = ChainGenerator.insert_dummy(dag, dag.get_top_hashes(), 4)

        # DagVisualizer.visualize(dag, True) # take a look to understand what's going on

        # there will be only two blocks with consecutive 4 behind, which is not enough to increase
        best_requirement = conf_req.choose_next_best_requirement(block_hash)
        self.assertEqual(best_requirement, 4)

        # make three blocks with consecutive 4 behind
        # it should lead to following block increasing requirement value
        conf_req.blocks[last_block_in_seq_hash] = 4
        best_requirement = conf_req.choose_next_best_requirement(block_hash)
        self.assertEqual(best_requirement, 5)

    def test_recursive_sequence_skips(self):
        dag = Dag(0)
        conf_req = ConfirmationRequirement(dag)

        genesis_hash = dag.genesis_block().get_hash()

        block_hash = ChainGenerator.insert_dummy(dag, [genesis_hash], 1)
        conf_req.blocks[block_hash] = 5
        block_hash = ChainGenerator.insert_dummy(dag, [block_hash], 5)

        # confirmation requirement decreases because we have large skip 
        confirmation_requirement = conf_req.get_confirmation_requirement(block_hash)
        self.assertEqual(confirmation_requirement, 4)

        block_hash = ChainGenerator.insert_dummy(dag, [block_hash], 9)

        # DagVisualizer.visualize(dag, True) # take a look to understand what's going on

        confirmation_requirement = conf_req.get_confirmation_requirement(block_hash)
        self.assertEqual(confirmation_requirement, 3)

    def test_skips_and_restoring(self):
        dag = Dag(0)
        conf_req = ConfirmationRequirement(dag)

        genesis_hash = dag.genesis_block().get_hash()

        block_hash = ChainGenerator.insert_dummy(dag, [genesis_hash], 1)
        conf_req.blocks[block_hash] = 5
        block_hash = ChainGenerator.insert_dummy(dag, [block_hash], 5)

        # confirmation requirement decreases because we have large skip 
        confirmation_requirement = conf_req.get_confirmation_requirement(block_hash)
        self.assertEqual(confirmation_requirement, 4)

        block_hash = ChainGenerator.insert_dummy(dag, [block_hash], 6)
        block_hash = ChainGenerator.insert_dummy(dag, [block_hash], 7)

        #we still have 4 here
        confirmation_requirement = conf_req.get_confirmation_requirement(block_hash)
        self.assertEqual(confirmation_requirement, 4)

        block_hash = ChainGenerator.insert_dummy(dag, [block_hash], 8)
        
        #but we have restored to 5 here, because of 3 previous consecutive blocks
        confirmation_requirement = conf_req.get_confirmation_requirement(block_hash)
        self.assertEqual(confirmation_requirement, 5)

        #let's skip one
        block_hash = ChainGenerator.insert_dummy(dag, [block_hash], 10)

        block_hash = ChainGenerator.insert_dummy(dag, [block_hash], 11)
        
        # DagVisualizer.visualize(dag, True) # take a look to understand what's going on

        #not affected by small skip
        confirmation_requirement = conf_req.get_confirmation_requirement(block_hash)
        self.assertEqual(confirmation_requirement, 5)

    def test_skip_confirmation_requirement(self):
        dag = Dag(0)
        conf_req = ConfirmationRequirement(dag)

        genesis_hash = dag.genesis_block().get_hash()

        block_hash = ChainGenerator.insert_dummy(dag, [genesis_hash], 1)
        # confirmation requirement decreases because we have large skip 
        confirmation_requirement = conf_req.get_confirmation_requirement(block_hash)
        self.assertEqual(confirmation_requirement, 5)

        block_hash = ChainGenerator.insert_dummy(dag, [block_hash], 3)
        skip = SkippedBlock(block_hash, 1)
        confirmation_requirement = conf_req.get_confirmation_requirement(skip)
        self.assertEqual(confirmation_requirement, 5)

        # do a larger gap
        block_hash = ChainGenerator.insert_dummy(dag, [block_hash], 11)

        confirmation_requirement = conf_req.get_confirmation_requirement(block_hash)
        self.assertEqual(confirmation_requirement, 3)

        confirmation_requirement = conf_req.get_confirmation_requirement(SkippedBlock(block_hash, 1))
        self.assertEqual(confirmation_requirement, 3)

        confirmation_requirement = conf_req.get_confirmation_requirement(SkippedBlock(block_hash, 2))
        self.assertEqual(confirmation_requirement, 4)

        confirmation_requirement = conf_req.get_confirmation_requirement(SkippedBlock(block_hash, 4))
        self.assertEqual(confirmation_requirement, 4)

        confirmation_requirement = conf_req.get_confirmation_requirement(SkippedBlock(block_hash, 5))
        self.assertEqual(confirmation_requirement, 5)

        confirmation_requirement = conf_req.get_confirmation_requirement(SkippedBlock(block_hash, 6))
        self.assertEqual(confirmation_requirement, 5)

        confirmation_requirement = conf_req.get_confirmation_requirement(SkippedBlock(block_hash, 10))
        self.assertEqual(confirmation_requirement, ZETA_MAX)


    #TODO complex cases