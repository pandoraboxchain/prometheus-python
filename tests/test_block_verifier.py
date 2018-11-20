import unittest

from hashlib import sha256

from chain.block_factory import BlockFactory
from chain.transaction_factory import TransactionFactory
from chain.dag import Dag
from crypto.private import Private
from chain.epoch import Epoch, BLOCK_TIME
from chain.dag import ChainIter
from verification.acceptor import AcceptionException
from verification.block_acceptor import BlockAcceptor
from tools.chain_generator import ChainGenerator


class TestBlockVerifier(unittest.TestCase):

    def test_sane_prev_hashes_found(self):
        dag = Dag(0)
        epoch = Epoch(dag)
        genesis_hash = dag.genesis_block().get_hash()

        block_hash1 = ChainGenerator.insert_dummy(dag, [genesis_hash], 1)
        block_hash2 = ChainGenerator.insert_dummy(dag, [block_hash1], 2)
        _block_hash3 = ChainGenerator.insert_dummy(dag, [genesis_hash, block_hash2], 3)

        verifier = BlockAcceptor(epoch, None)

        with self.assertRaises(AcceptionException):
            verifier.validate_non_ancestor_prev_hashes([genesis_hash, block_hash2])

    def test_sane_prev_hashes_not_found(self):
        dag = Dag(0)
        epoch = Epoch(dag)
        genesis_hash = dag.genesis_block().get_hash()

        block_hash1 = ChainGenerator.insert_dummy(dag, [genesis_hash], 1)
        block_hash2 = ChainGenerator.insert_dummy(dag, [block_hash1], 2)
        block_hash3 = ChainGenerator.insert_dummy(dag, [genesis_hash], 3)
        _block_hash4 = ChainGenerator.insert_dummy(dag, [block_hash2, block_hash3], 4)

        verifier = BlockAcceptor(epoch, None)

        try:
            verifier.validate_non_ancestor_prev_hashes([block_hash2, block_hash3])
        except:
            self.fail("Prev hashes should not be self referential")

    