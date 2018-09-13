import unittest
import os

from chain.node import Node
from tests.test_chain_generator import TestChainGenerator
from tools.time import Time

class Node(unittest.TestCase):
    def test_time_advancer(self):

        Time.use_test_time()

        Time.set_current_time(7)
        self.assertEqual(Time.get_current_time(), 7)
        
        Time.advance_block_time()
        self.assertEqual(Time.get_current_time(), 11)


