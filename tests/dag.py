import unittest
from chain.block_factory import BlockFactory
from chain.transaction_factory import TransactionFactory
from chain.dag import Dag
from crypto.private import Private
from chain.epoch import BLOCK_TIME
from chain.dag import ChainIter
from tests.test_chain_generator import TestChainGenerator


class TestDag(unittest.TestCase):

    def test_top_blocks(self):
        dag = Dag(0)
        private = Private.generate()
        block1 = BlockFactory.create_block_with_timestamp([dag.genesis_block().get_hash()], BLOCK_TIME)
        signed_block1 = BlockFactory.sign_block(block1, private)
        dag.add_signed_block(1, signed_block1)

        block2 = BlockFactory.create_block_with_timestamp([block1.get_hash()], BLOCK_TIME * 2)
        signed_block2 = BlockFactory.sign_block(block2, private)
        dag.add_signed_block(2, signed_block2)

        block3 = BlockFactory.create_block_with_timestamp([block1.get_hash()], BLOCK_TIME * 3)
        signed_block3 = BlockFactory.sign_block(block3, private)
        dag.add_signed_block(3, signed_block3)

        top_hashes = dag.get_top_blocks_hashes()

        self.assertEqual(top_hashes[0], block2.get_hash())
        self.assertEqual(top_hashes[1], block3.get_hash())

    def test_chain_length(self):
        dag = Dag(0)
        private = Private.generate()
        block1 = BlockFactory.create_block_with_timestamp([dag.genesis_block().get_hash()], BLOCK_TIME)
        signed_block1 = BlockFactory.sign_block(block1, private)
        dag.add_signed_block(1, signed_block1)

        block2 = BlockFactory.create_block_with_timestamp([block1.get_hash()], BLOCK_TIME * 2)
        signed_block2 = BlockFactory.sign_block(block2, private)
        dag.add_signed_block(2, signed_block2)

        block3 = BlockFactory.create_block_with_timestamp([block2.get_hash()], BLOCK_TIME * 3)
        signed_block3 = BlockFactory.sign_block(block3, private)
        dag.add_signed_block(3, signed_block3)

        # alternative chain
        other_block2 = BlockFactory.create_block_with_timestamp([block1.get_hash()], BLOCK_TIME * 2 + 1)
        other_signed_block2 = BlockFactory.sign_block(other_block2, private)
        dag.add_signed_block(2, other_signed_block2)

        self.assertEqual(dag.calculate_chain_length(other_block2.get_hash()), 3)
        self.assertEqual(dag.calculate_chain_length(block3.get_hash()), 4)

    def test_ancestry(self):
        dag = Dag(0)
        private = Private.generate()
        block1 = BlockFactory.create_block_with_timestamp([dag.genesis_block().get_hash()], BLOCK_TIME)
        signed_block1 = BlockFactory.sign_block(block1, private)
        dag.add_signed_block(1, signed_block1)

        block2 = BlockFactory.create_block_with_timestamp([block1.get_hash()], BLOCK_TIME * 2)
        signed_block2 = BlockFactory.sign_block(block2, private)
        dag.add_signed_block(2, signed_block2)

        block3 = BlockFactory.create_block_with_timestamp([block2.get_hash()], BLOCK_TIME * 3)
        signed_block3 = BlockFactory.sign_block(block3, private)
        dag.add_signed_block(3, signed_block3)

        # alternative chain
        other_block2 = BlockFactory.create_block_with_timestamp([block1.get_hash()], BLOCK_TIME * 2 + 1)
        other_signed_block2 = BlockFactory.sign_block(other_block2, private)
        dag.add_signed_block(2, other_signed_block2)

        # alternative chain
        other_block3 = BlockFactory.create_block_with_timestamp([other_block2.get_hash()], BLOCK_TIME * 3 + 1)
        other_signed_block3 = BlockFactory.sign_block(other_block3, private)
        dag.add_signed_block(3, other_signed_block3)
        
        self.assertEqual(dag.is_ancestor(other_block3.get_hash(), other_block2.get_hash()), True)
        self.assertEqual(dag.is_ancestor(other_block3.get_hash(), block2.get_hash()), False)

    def test_iterator(self):
        dag = Dag(0)
        private = Private.generate()
        block1 = BlockFactory.create_block_with_timestamp([dag.genesis_block().get_hash()], BLOCK_TIME)
        signed_block1 = BlockFactory.sign_block(block1, private)
        dag.add_signed_block(1, signed_block1)

        block2 = BlockFactory.create_block_with_timestamp([block1.get_hash()], BLOCK_TIME * 2)
        signed_block2 = BlockFactory.sign_block(block2, private)
        dag.add_signed_block(2, signed_block2)

        block3 = BlockFactory.create_block_with_timestamp([block2.get_hash()], BLOCK_TIME * 3)
        signed_block3 = BlockFactory.sign_block(block3, private)
        dag.add_signed_block(3, signed_block3)

        # alternative chain
        other_block2 = BlockFactory.create_block_with_timestamp([block1.get_hash()], BLOCK_TIME * 2 + 1)
        other_signed_block2 = BlockFactory.sign_block(other_block2, private)
        dag.add_signed_block(2, other_signed_block2)

        # intentionally skipped block

        # alternative chain
        other_block4 = BlockFactory.create_block_with_timestamp([other_block2.get_hash()], BLOCK_TIME * 3 + 1)
        other_signed_block4 = BlockFactory.sign_block(other_block4, private)
        dag.add_signed_block(4, other_signed_block4)

        chain_iter = ChainIter(dag, block3.get_hash())
        self.assertEqual(chain_iter.next().block.get_hash(), block3.get_hash())
        self.assertEqual(chain_iter.next().block.get_hash(), block2.get_hash())
        self.assertEqual(chain_iter.next().block.get_hash(), block1.get_hash())

        chain_iter = ChainIter(dag, other_block4.get_hash())
        self.assertEqual(chain_iter.next().block.get_hash(), other_block4.get_hash())
        self.assertEqual(chain_iter.next(), None)   # detect intentionally skipped block
        self.assertEqual(chain_iter.next().block.get_hash(), other_block2.get_hash())
        self.assertEqual(chain_iter.next().block.get_hash(), block1.get_hash())

    def test_top_blocks_in_range(self):
        dag = Dag(0)

        prev_hash = dag.genesis_block().get_hash()
        TestChainGenerator.fill_with_dummies_and_skips(dag, prev_hash, range(1,8), [3,5])
        TestChainGenerator.fill_with_dummies_and_skips(dag, prev_hash, range(1,8), [4])
        TestChainGenerator.fill_with_dummies_and_skips(dag, prev_hash, range(1,7), [4,5])

        tops = dag.get_branches_for_timeslot_range(3, 6)

        self.assertEqual(len(tops), 3)
        self.assertIn(dag.blocks_by_number[4][0].get_hash(), tops)
        self.assertIn(dag.blocks_by_number[5][0].get_hash(), tops)
        self.assertIn(dag.blocks_by_number[3][1].get_hash(), tops)

        tops = dag.get_branches_for_timeslot_range(4, 5)

        self.assertEqual(len(tops), 1)
        self.assertIn(dag.blocks_by_number[4][0].get_hash(), tops)

        tops = dag.get_branches_for_timeslot_range(3, 5)
        self.assertEqual(len(tops), 3)
        self.assertIn(dag.blocks_by_number[4][0].get_hash(), tops)
        self.assertIn(dag.blocks_by_number[3][0].get_hash(), tops)
        self.assertIn(dag.blocks_by_number[3][1].get_hash(), tops)

    def test_storing_tx_by_hash(self):
        dag = Dag(0)
        private0 = Private.generate()
        private1 = Private.generate()
        private2 = Private.generate()

        # add block 1
        block1 = BlockFactory.create_block_with_timestamp([dag.genesis_block().get_hash()], BLOCK_TIME)
        signed_block1 = BlockFactory.sign_block(block1, private0)
        dag.add_signed_block(1, signed_block1)

        # check transactions in dag.transactions_by_hash for empty
        self.assertTrue(len(dag.transactions_by_hash) == 0)

        # add block 2
        block2 = BlockFactory.create_block_with_timestamp([block1.get_hash()], BLOCK_TIME)
        # add penalty gossip case by tx in block
        tx1 = TransactionFactory.create_negative_gossip_transaction(1, private1)
        tx2 = TransactionFactory.create_positive_gossip_transaction(block2.get_hash(), private1)
        block2.system_txs.append(tx1)
        block2.system_txs.append(tx2)
        # --------------------------------------
        signed_block2 = BlockFactory.sign_block(block2, private1)
        dag.add_signed_block(2, signed_block2)

        # check transactions in dag.transactions_by_hash
        self.assertTrue(set(dag.transactions_by_hash).issuperset({tx1.get_hash(): tx1}))
        self.assertTrue(set(dag.transactions_by_hash).issuperset({tx2.get_hash(): tx2}))

        block3 = BlockFactory.create_block_with_timestamp([block2.get_hash()], BLOCK_TIME)
        signed_block3 = BlockFactory.sign_block(block3, private2)
        dag.add_signed_block(3, signed_block3)

        # check transactions in dag.transactions_by_hash
        self.assertTrue(set(dag.transactions_by_hash).issuperset({tx1.get_hash(): tx1}))
        self.assertTrue(set(dag.transactions_by_hash).issuperset({tx2.get_hash(): tx2}))

    def test_getting_tx_by_hash(self):
        dag = Dag(0)
        private = Private.generate()

        block1 = BlockFactory.create_block_with_timestamp([dag.genesis_block().get_hash()], BLOCK_TIME)
        tx1 = TransactionFactory.create_negative_gossip_transaction(1, private)
        tx2 = TransactionFactory.create_positive_gossip_transaction(block1.get_hash(), private)
        tx3 = TransactionFactory.create_penalty_gossip_transaction({tx1.get_hash(): tx2.get_hash()}, private)
        not_appended_tx = TransactionFactory.create_public_key_transaction(Private.generate(), private)
        block1.system_txs.append(tx1)
        block1.system_txs.append(tx2)
        block1.system_txs.append(tx3)

        signed_block1 = BlockFactory.sign_block(block1, private)
        dag.add_signed_block(1, signed_block1)

        self.assertTrue(set(dag.transactions_by_hash).issuperset({tx1.get_hash(): tx1}))
        self.assertTrue(set(dag.transactions_by_hash).issuperset({tx2.get_hash(): tx2}))
        self.assertTrue(set(dag.transactions_by_hash).issuperset({tx3.get_hash(): tx3}))
        self.assertFalse(set(dag.transactions_by_hash).issuperset({not_appended_tx.get_hash(): not_appended_tx}))

        # test dag.tx_by_hash getter
        self.assertTrue(dag.get_tx_by_hash(tx1.get_hash()) == tx1)
        self.assertTrue(dag.get_tx_by_hash(tx2.get_hash()) == tx2)
        self.assertTrue(dag.get_tx_by_hash(tx3.get_hash()) == tx3)

        # if ask wrong tx_hash
        # dag.get_tx_by_hash(not_appended_tx.get_hash())
        # AssertionError('Cant find tx by hash', not_appended_tx.get_hash()))

