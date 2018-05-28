import unittest
from chain.block import Block
from chain.dag import Dag

class TestEra(unittest.TestCase):

    def test_genesis_is_first_era_hash(self):
        dag = Dag(0)

        first_era_hash = dag.get_era_hash(1)
        genesis_hash = dag.genesis_block().get_hash().digest()

        self.assertEqual(first_era_hash, genesis_hash)
