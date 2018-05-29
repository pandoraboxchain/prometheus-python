import unittest
from chain.block import Block
from chain.dag import Dag
from chain.epoch import Epoch

class TestEpoch(unittest.TestCase):

    def test_genesis_is_first_epoch_hash(self):
        dag = Dag(0)
        epoch = Epoch(dag)

        first_era_hash = epoch.get_epoch_hash(1)
        genesis_hash = dag.genesis_block().get_hash().digest()

        self.assertEqual(first_era_hash, genesis_hash)
