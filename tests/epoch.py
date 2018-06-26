import unittest
import random
import os

from Crypto.Hash import SHA256
from base64 import b64encode

from chain.block import Block
from chain.signed_block import SignedBlock
from chain.dag import Dag
from chain.epoch import Epoch, Round, RoundIter, BLOCK_TIME
from chain.block_factory import BlockFactory
from transaction.transaction import PublicKeyTransaction, PrivateKeyTransaction, SplitRandomTransaction
from crypto.dec_part_random import dec_part_random
from crypto.enc_random import enc_part_random, encode_value
from crypto.sum_random import sum_random, calculate_validators_numbers
from crypto.private import Private
from crypto.secret import split_secret, encode_splits, decode_random
from crypto.keys import Keys

from tests.test_chain_generator import TestChainGenerator

class TestEpoch(unittest.TestCase):

    def test_genesis_is_first_epoch_hash(self):
        dag = Dag(0)
        epoch = Epoch(dag)

        first_era_hash = epoch.get_epoch_hash(1)
        genesis_hash = dag.genesis_block().get_hash()

        self.assertEqual(first_era_hash, genesis_hash)

    def test_rounds(self):
        dag = Dag(0)
        epoch = Epoch(dag)

        node_private_key = Private.generate()

        private_keys = []

        block_number = 1

        for i in range(0, Round.PUBLIC_DURATION):
            private = Private.generate()
            pubkey_tx = PublicKeyTransaction()
            pubkey_tx.generated_pubkey = b64encode(private.publickey().exportKey('DER'))
            pubkey_tx.sender_pubkey = b64encode(node_private_key.publickey().exportKey('DER'))
            pubkey_tx.signature = node_private_key.sign(pubkey_tx.get_hash(), 0)[0]
            public_key_block = Block()
            public_key_block.timestamp = block_number * BLOCK_TIME
            public_key_block.prev_hashes = dag.get_top_blocks_hashes()
            public_key_block.system_txs = [pubkey_tx]
            signed_block = BlockFactory.sign_block(public_key_block, node_private_key)
            dag.add_signed_block(block_number, signed_block)
            block_number += 1

            private_keys.append(private)

        public_keys = []
        for private in private_keys:
            public_keys.append(private.publickey())

        randoms_list = []
        expected_random_pieces = []
        for i in range(0, Round.RANDOM_DURATION):
            random_bytes = os.urandom(32)
            random_value = int.from_bytes(random_bytes, byteorder='big')
            split_random_tx = SplitRandomTransaction()
            splits = split_secret(random_bytes, 2, 3)
            encoded_splits = encode_splits(splits, public_keys)
            split_random_tx.pieces = encoded_splits
            expected_random_pieces.append(split_random_tx.pieces)
            split_random_tx.signature = node_private_key.sign(pubkey_tx.get_hash(), 0)[0]
            split_random_block = Block()
            split_random_block.timestamp = block_number * BLOCK_TIME
            split_random_block.prev_hashes = dag.get_top_blocks_hashes()
            split_random_block.system_txs = [split_random_tx]
            signed_block = BlockFactory.sign_block(split_random_block, node_private_key)
            dag.add_signed_block(block_number, signed_block)
            randoms_list.append(random_value)
            block_number += 1

        expected_seed = sum_random(randoms_list)  

        raw_private_keys = []
        for private in private_keys:
            private_key_tx = PrivateKeyTransaction()
            private_key_tx.key = b64encode(private.exportKey('DER'))
            raw_private_keys.append(private_key_tx.key)
            private_key_block = Block()
            private_key_block.system_txs = [private_key_tx]
            private_key_block.prev_hashes = dag.get_top_blocks_hashes()
            private_key_block.timestamp = block_number * BLOCK_TIME            
            signed_block = BlockFactory.sign_block(private_key_block, private)
            dag.add_signed_block(block_number, signed_block)            
            block_number += 1
        
        top_block_hash = dag.get_top_blocks_hashes()[0]

        random_splits = epoch.get_random_splits_for_epoch_from_block(top_block_hash)
        self.assertEqual(expected_random_pieces, random_splits)

        restored_randoms = []
        for i in range(0, len(random_splits)):
            random = decode_random(random_splits[i], Keys.list_from_bytes(raw_private_keys))
            restored_randoms.append(random)

        self.assertEqual(randoms_list, restored_randoms)

        seed = epoch.calculate_epoch_seed(2)
        self.assertEqual(expected_seed, seed)

    def test_epoch_number(self):
        epoch = Epoch(Dag(0))
        self.assertEqual(epoch.get_epoch_number(6), 1)
        self.assertEqual(epoch.get_epoch_number(10), 2)
        self.assertEqual(epoch.get_epoch_start_block_number(2), 10)
        self.assertEqual(epoch.convert_to_epoch_block_number(10), 0)
        self.assertEqual(epoch.convert_to_epoch_block_number(12), 2)
        self.assertEqual(Epoch.get_round_by_block_number(7), Round.PRIVATE)
        self.assertEqual(Epoch.get_round_by_block_number(8), Round.PRIVATE)
        self.assertEqual(Epoch.get_round_by_block_number(9), Round.PRIVATE)

    def test_round_durations(self):
        self.assertEqual(Epoch.get_range_for_round(1, Round.PUBLIC), (1,3))
        self.assertEqual(Epoch.get_range_for_round(1, Round.RANDOM), (4,6))
        self.assertEqual(Epoch.get_range_for_round(1, Round.PRIVATE), (7,9))

    def test_round_iterator(self):
        dag = TestChainGenerator.generate_two_chains(9)

        main_top = dag.blocks_by_number[9][0]

        round_iter = RoundIter(dag, main_top.get_hash(), Round.PUBLIC)
        self.assertEqual(round_iter.next().get_hash(), dag.blocks_by_number[3][0].get_hash())
        self.assertEqual(round_iter.next().get_hash(), dag.blocks_by_number[2][0].get_hash())
        self.assertEqual(round_iter.next().get_hash(), dag.blocks_by_number[1][0].get_hash())

        off_chain_top = dag.blocks_by_number[9][1]

        round_iter = RoundIter(dag, off_chain_top.get_hash(), Round.RANDOM)
        self.assertEqual(round_iter.next().get_hash(), dag.blocks_by_number[6][1].get_hash())
        self.assertEqual(round_iter.next().get_hash(), dag.blocks_by_number[5][1].get_hash())
        self.assertEqual(round_iter.next(), None)   #detect intentionally skipped block

        round_iter = RoundIter(dag, off_chain_top.get_hash(), Round.PRIVATE)
        self.assertEqual(round_iter.next().get_hash(), dag.blocks_by_number[9][1].get_hash())
        self.assertEqual(round_iter.next().get_hash(), dag.blocks_by_number[8][1].get_hash())
        self.assertEqual(round_iter.next().get_hash(), dag.blocks_by_number[7][1].get_hash())