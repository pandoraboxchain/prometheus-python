import unittest

from node.block_signers import BlockSigners
from node.validators import Validators
from tools.time import Time
from chain.epoch import Epoch


class TestNodeOffline(unittest.TestCase):

    def test_node_offline(self):
        Time.use_test_time()
        Time.set_current_time(1)

        private_keys = BlockSigners()
        private_keys = private_keys.block_signers

        validators = Validators()
        validators.validators = Validators.read_genesis_validators_from_file()
        validators.signers_order = [0] + [1] + [2] * Epoch.get_duration()
        validators.randomizers_order = [0] * Epoch.get_duration()


