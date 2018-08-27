import unittest
import random
import os

from Crypto.Hash import SHA256
from base64 import b64encode

from chain.block import Block
from chain.signed_block import SignedBlock
from chain.dag import Dag
from chain.epoch import Epoch, RoundIter, BLOCK_TIME
from chain.params import Round, Duration
from chain.block_factory import BlockFactory
from transaction.transaction import PublicKeyTransaction, PrivateKeyTransaction, SplitRandomTransaction
from transaction.transaction import CommitRandomTransaction, RevealRandomTransaction
from crypto.dec_part_random import dec_part_random
from crypto.enc_random import enc_part_random
from crypto.sum_random import sum_random, calculate_validators_indexes
from crypto.private import Private
from crypto.secret import split_secret, encode_splits, decode_random
from crypto.keys import Keys
from chain.params import ROUND_DURATION

from tests.test_chain_generator import TestChainGenerator

class TestEpoch(unittest.TestCase):

    def test_genesis_is_first_epoch_hash(self):
        dag = Dag(0)
        epoch = Epoch(dag)

        first_era_hash = epoch.get_epoch_hash(1)
        genesis_hash = dag.genesis_block().get_hash()

        self.assertEqual(first_era_hash, genesis_hash)

    def test_secret_sharing_rounds(self):
        dag = Dag(0)
        epoch = Epoch(dag)

        dummy_private = Private.generate()

        signers = []
        for i in range(0, ROUND_DURATION + 1):
            signers.append(Private.generate())

        private_keys = []

        block_number = 1
        prev_hash = dag.genesis_block().get_hash()
        signer_index = 0
        for i in Epoch.get_round_range(1, Round.PUBLIC):
            private = Private.generate()
            private_keys.append(private)

            signer = signers[signer_index]
            pubkey_tx = PublicKeyTransaction()
            pubkey_tx.generated_pubkey = Keys.to_bytes(private.publickey())
            pubkey_tx.sender_pubkey = Keys.to_bytes(signer.publickey())
            pubkey_tx.signature = signer.sign(pubkey_tx.get_hash(), 0)[0]

            block = Block()
            block.timestamp = i * BLOCK_TIME
            block.prev_hashes = [prev_hash]
            block.system_txs = [pubkey_tx]
            signed_block = BlockFactory.sign_block(block, signer)
            dag.add_signed_block(i, signed_block)
            signer_index += 1
            prev_hash = block.get_hash()

        prev_hash = TestChainGenerator.fill_with_dummies(dag, prev_hash, Epoch.get_round_range(1, Round.COMMIT))

        public_keys = []
        for private in private_keys:
            public_keys.append(private.publickey())

        randoms_list = []
        expected_random_pieces = []
        for i in Epoch.get_round_range(1, Round.SECRETSHARE):
            random_bytes = os.urandom(32)
            random_value = int.from_bytes(random_bytes, byteorder='big')
            split_random_tx = SplitRandomTransaction()
            splits = split_secret(random_bytes, 2, 3)
            encoded_splits = encode_splits(splits, public_keys)
            split_random_tx.pieces = encoded_splits
            expected_random_pieces.append(split_random_tx.pieces)
            split_random_tx.signature = dummy_private.sign(pubkey_tx.get_hash(), 0)[0]
            block = Block()
            block.timestamp = i * BLOCK_TIME
            block.prev_hashes = [prev_hash]
            block.system_txs = [split_random_tx]
            signed_block = BlockFactory.sign_block(block, dummy_private)
            dag.add_signed_block(i, signed_block)
            randoms_list.append(random_value)
            prev_hash = block.get_hash()

        expected_seed = sum_random(randoms_list)  

        prev_hash = TestChainGenerator.fill_with_dummies(dag, prev_hash, Epoch.get_round_range(1, Round.REVEAL))

        signer_index = 0
        private_key_index = 0
        raw_private_keys = []
        for i in Epoch.get_round_range(1, Round.PRIVATE):
            private_key_tx = PrivateKeyTransaction()
            private_key_tx.key = Keys.to_bytes(private_keys[private_key_index])
            raw_private_keys.append(private_key_tx.key)
            signer = signers[signer_index]
            block = Block()
            block.system_txs = [private_key_tx]
            block.prev_hashes = [prev_hash]
            block.timestamp = block_number * BLOCK_TIME            
            signed_block = BlockFactory.sign_block(block, signer)
            dag.add_signed_block(i, signed_block)          
            signer_index += 1
            private_key_index += 1
            prev_hash = block.get_hash()
        
        prev_hash = TestChainGenerator.fill_with_dummies(dag, prev_hash, Epoch.get_round_range(1, Round.FINAL))

        top_block_hash = dag.get_top_blocks_hashes()[0]

        random_splits = epoch.get_random_splits_for_epoch(top_block_hash)
        self.assertEqual(expected_random_pieces, random_splits)

        restored_randoms = []
        for i in range(0, len(random_splits)):
            random = decode_random(random_splits[i], Keys.list_from_bytes(raw_private_keys))
            restored_randoms.append(random)

        self.assertEqual(randoms_list, restored_randoms)

        seed = epoch.extract_shared_random(top_block_hash)
        self.assertEqual(expected_seed, seed)

    def test_commit_reveal(self):
        dag = Dag(0)
        epoch = Epoch(dag)

        private = Private.generate()

        prev_hash = TestChainGenerator.fill_with_dummies(dag, dag.genesis_block().get_hash(), Epoch.get_round_range(1, Round.PUBLIC))

        randoms_list = []
        for i in Epoch.get_round_range(1, Round.COMMIT):
            random_value = int.from_bytes(os.urandom(32), byteorder='big')
            randoms_list.append(random_value)

        expected_seed = sum_random(randoms_list)

        reveals = []

        epoch_hash = epoch.get_epoch_hash(1)

        for i in Epoch.get_round_range(1, Round.COMMIT):
            rand = randoms_list.pop()
            random_bytes = rand.to_bytes(32, byteorder='big')
            commit, reveal = TestEpoch.create_dummy_commit_reveal(random_bytes, epoch_hash)
            commit_block = BlockFactory.create_block_with_timestamp([prev_hash], i * BLOCK_TIME)
            commit_block.system_txs = [commit]
            signed_block = BlockFactory.sign_block(commit_block, private)
            dag.add_signed_block(i, signed_block)
            prev_hash = commit_block.get_hash()
            reveals.append(reveal)

            revealing_key = Keys.from_bytes(reveal.key)
            encrypted_bytes = revealing_key.publickey().encrypt(random_bytes, 32)[0]
            decrypted_bytes = revealing_key.decrypt(encrypted_bytes)
            self.assertEqual(decrypted_bytes, random_bytes)

            revealed_value = revealing_key.decrypt(commit.rand)
            self.assertEqual(revealed_value, random_bytes)

        # self.assertEqual(len(reveals), ROUND_DURATION)

        prev_hash = TestChainGenerator.fill_with_dummies(dag, prev_hash, Epoch.get_round_range(1, Round.SECRETSHARE))

        for i in Epoch.get_round_range(1, Round.REVEAL):
            reveal_block = BlockFactory.create_block_with_timestamp([prev_hash], i * BLOCK_TIME)
            reveal_block.system_txs = [reveals.pop()]
            signed_block = BlockFactory.sign_block(reveal_block, private)
            dag.add_signed_block(i, signed_block)
            prev_hash = reveal_block.get_hash()           

        prev_hash = TestChainGenerator.fill_with_dummies(dag, prev_hash, Epoch.get_round_range(1, Round.PRIVATE))

        prev_hash = TestChainGenerator.fill_with_dummies(dag, prev_hash, Epoch.get_round_range(1, Round.FINAL))

        seed = epoch.reveal_commited_random(prev_hash)
        self.assertEqual(expected_seed, seed)

    def test_epoch_number(self):
        epoch = Epoch(Dag(0))
        self.assertEqual(Epoch.get_duration(), 19)
        self.assertEqual(Epoch.get_epoch_number(6), 1)
        self.assertEqual(Epoch.get_epoch_number(19), 1)
        self.assertEqual(Epoch.get_epoch_number(20), 2)
        self.assertEqual(Epoch.get_epoch_start_block_number(2), 20)
        self.assertEqual(Epoch.get_epoch_end_block_number(1), 19)
        self.assertEqual(Epoch.convert_to_epoch_block_number(13), 12)
        self.assertEqual(Epoch.convert_to_epoch_block_number(20), 0)
        self.assertEqual(Epoch.convert_to_epoch_block_number(26), 6)
        self.assertEqual(Epoch.get_round_by_block_number(1), Round.PUBLIC)
        self.assertEqual(Epoch.get_round_by_block_number(4), Round.COMMIT)
        self.assertEqual(Epoch.get_round_by_block_number(7), Round.SECRETSHARE)
        self.assertEqual(Epoch.get_round_by_block_number(10), Round.REVEAL)
        self.assertEqual(Epoch.get_round_by_block_number(14), Round.PRIVATE)
        self.assertEqual(Epoch.get_round_by_block_number(16), Round.FINAL)

    def test_round_durations(self):
        self.assertEqual(Epoch.get_round_bounds(1, Round.PUBLIC), (1,3))
        self.assertEqual(Epoch.get_round_bounds(1, Round.COMMIT), (4,6))
        self.assertEqual(Epoch.get_round_bounds(1, Round.SECRETSHARE), (7,9))
        self.assertEqual(Epoch.get_round_bounds(1, Round.REVEAL), (10,12))
        self.assertEqual(Epoch.get_round_bounds(1, Round.PRIVATE), (13,15))
        self.assertEqual(Epoch.get_round_bounds(1, Round.FINAL), (16,19))

    def test_round_iterator(self):
        dag = TestChainGenerator.generate_two_chains(9)

        # from visualization.dag_visualizer import DagVisualizer
        # DagVisualizer.visualize(dag)

        main_top = dag.blocks_by_number[9][0]

        round_iter = RoundIter(dag, main_top.get_hash(), Round.PUBLIC)
        self.assertEqual(round_iter.next().get_hash(), dag.blocks_by_number[3][0].get_hash())
        self.assertEqual(round_iter.next().get_hash(), dag.blocks_by_number[2][0].get_hash())
        self.assertEqual(round_iter.next().get_hash(), dag.blocks_by_number[1][0].get_hash())

        off_chain_top = dag.blocks_by_number[9][1]

        round_iter = RoundIter(dag, off_chain_top.get_hash(), Round.COMMIT)
        self.assertEqual(round_iter.next().get_hash(), dag.blocks_by_number[6][1].get_hash())
        self.assertEqual(round_iter.next().get_hash(), dag.blocks_by_number[5][1].get_hash())
        self.assertEqual(round_iter.next(), None)   #detect intentionally skipped block

        round_iter = RoundIter(dag, off_chain_top.get_hash(), Round.SECRETSHARE)
        self.assertEqual(round_iter.next().get_hash(), dag.blocks_by_number[9][1].get_hash())
        self.assertEqual(round_iter.next().get_hash(), dag.blocks_by_number[8][1].get_hash())
        self.assertEqual(round_iter.next().get_hash(), dag.blocks_by_number[7][1].get_hash())

    def test_top_blocks(self):
        dag = Dag(0)
        epoch = Epoch(dag)
        dag.subscribe_to_new_block_notification(epoch)
        private = Private.generate()
        
        epoch_hash = dag.genesis_block().get_hash()
        
        self.assertEqual(dag.genesis_block().get_hash(), list(epoch.get_epoch_hashes().keys())[0])
        self.assertEqual(dag.genesis_block().get_hash(), list(epoch.get_epoch_hashes().values())[0])

        block1 = BlockFactory.create_block_with_timestamp([dag.genesis_block().get_hash()], BLOCK_TIME)
        signed_block1 = BlockFactory.sign_block(block1, private)
        dag.add_signed_block(1, signed_block1)

        self.assertEqual(block1.get_hash(), list(epoch.get_epoch_hashes().keys())[0])
        self.assertEqual(epoch_hash, list(epoch.get_epoch_hashes().values())[0])

        prev_hash = block1.get_hash()
        for i in range(2, 20):
            block = BlockFactory.create_block_with_timestamp([prev_hash], BLOCK_TIME * i)
            signed_block = BlockFactory.sign_block(block, private)
            dag.add_signed_block(i, signed_block)
            prev_hash = block.get_hash()

        if epoch.is_new_epoch_upcoming(20):
            epoch.accept_tops_as_epoch_hashes()

        top_block_hash = dag.blocks_by_number[19][0].get_hash()
        epoch_hash = dag.blocks_by_number[19][0].get_hash()

        self.assertEqual(top_block_hash, list(epoch.get_epoch_hashes().keys())[0])
        self.assertEqual(epoch_hash, list(epoch.get_epoch_hashes().values())[0])

        for i in range(20, 39):
            block = BlockFactory.create_block_with_timestamp([prev_hash], BLOCK_TIME * i)
            signed_block = BlockFactory.sign_block(block, private)
            dag.add_signed_block(i, signed_block)
            prev_hash = block.get_hash()

        if epoch.is_new_epoch_upcoming(39):
            epoch.accept_tops_as_epoch_hashes()

        top_block_hash = dag.blocks_by_number[38][0].get_hash()
        epoch_hash = dag.blocks_by_number[38][0].get_hash()

        self.assertEqual(top_block_hash, list(epoch.get_epoch_hashes().keys())[0])
        self.assertEqual(epoch_hash, list(epoch.get_epoch_hashes().values())[0])

    def test_private_keys_extraction(self):
        dag = Dag(0)
        epoch = Epoch(dag)
        dag.subscribe_to_new_block_notification(epoch)
        node_private = Private.generate()

        prev_hash = dag.genesis_block().get_hash()
        round_start, round_end = Epoch.get_round_bounds(1, Round.PRIVATE)
        for i in range(1, round_start):
            block = BlockFactory.create_block_with_timestamp([prev_hash], BLOCK_TIME * i)
            signed_block = BlockFactory.sign_block(block, node_private)
            dag.add_signed_block(i, signed_block)
            prev_hash = block.get_hash()

        generated_private_keys = []
        for i in range(round_start, round_end): #intentionally skip last block of round
            generated_private = Private.generate()
            generated_private_keys.append(Keys.to_bytes(generated_private))

            private_key_tx = PrivateKeyTransaction()
            private_key_tx.key = Keys.to_bytes(generated_private)
            block = Block()
            block.system_txs = [private_key_tx]
            block.prev_hashes = dag.get_top_blocks_hashes()
            block.timestamp = i * BLOCK_TIME            
            signed_block = BlockFactory.sign_block(block, node_private)
            dag.add_signed_block(i, signed_block)
            prev_hash = block.get_hash()

        TestChainGenerator.fill_with_dummies(dag,prev_hash, Epoch.get_round_range(1, Round.FINAL))

        epoch_hash = dag.blocks_by_number[19][0].get_hash()

        extracted_privates = epoch.get_private_keys_for_epoch(epoch_hash)

        self.assertEqual(extracted_privates[0], generated_private_keys[0])
        self.assertEqual(extracted_privates[1], generated_private_keys[1])
        self.assertEqual(extracted_privates[2], None)

    #TODO use method for creating commit-reveal pair from Node.py
    @staticmethod
    def create_dummy_commit_reveal(random_bytes, epoch_hash):
        node_private = Private.generate()
        node_public = node_private.publickey()
        
        private = Private.generate()
        public = private.publickey()

        encoded = public.encrypt(random_bytes, 32)[0]

        commit = CommitRandomTransaction()
        commit.rand = encoded
        commit.pubkey = Keys.to_bytes(node_public)
        commit.signature = node_private.sign(commit.get_signing_hash(epoch_hash), 0)[0]

        reveal = RevealRandomTransaction()
        reveal.commit_hash = commit.get_reference_hash()
        reveal.key = Keys.to_bytes(private)

        return (commit, reveal)