import unittest
import random
import os

from Crypto.Hash import SHA256
from base64 import b64encode

from chain.block import Block
from chain.signed_block import SignedBlock
from chain.dag import Dag
from chain.epoch import Epoch, Round, BLOCK_TIME
from chain.block_factory import BlockFactory
from transaction.transaction import CommitRandomTransaction, RevealRandomTransaction
from crypto.dec_part_random import dec_part_random
from crypto.enc_random import enc_part_random, encode_value
from crypto.sum_random import sum_random, calculate_validators_numbers
from crypto.private import Private

class TestEpoch(unittest.TestCase):

    def test_genesis_is_first_epoch_hash(self):
        dag = Dag(0)
        epoch = Epoch(dag)

        first_era_hash = epoch.get_epoch_hash(1)
        genesis_hash = dag.genesis_block().get_hash().digest()

        self.assertEqual(first_era_hash, genesis_hash)

    def test_commit_reveal_validators_list(self):
        dag = Dag(0)
        epoch = Epoch(dag)

        private = Private.generate()

        randoms_list = []
        for i in range(0, Round.COMMIT_DURATION):
            random_value = int.from_bytes(os.urandom(32), byteorder='big')       
            randoms_list.append(random_value)

        expected_seed = sum_random(randoms_list)

        reveals = []
        block_number = 1

        epoch_hash = epoch.get_epoch_hash(1)

        for rand in randoms_list:
            commit, reveal = TestEpoch.create_dummy_commit_reveal(epoch_hash, rand)
            commit_block = Block()
            commit_block.timestamp = block_number * BLOCK_TIME
            commit_block.prev_hashes = dag.get_top_blocks()
            commit_block.system_txs = [commit]
            signed_block = BlockFactory.sign_block(commit_block, private)
            dag.add_signed_block(block_number, signed_block)
            block_number += 1

            reveals.append(reveal)

        self.assertEqual(len(reveals), Round.REVEAL_DURATION)

        for reveal in reveals:
            reveal_block = Block()
            reveal_block.system_txs = [reveal]
            reveal_block.prev_hashes = dag.get_top_blocks()
            reveal_block.timestamp = block_number * BLOCK_TIME            
            signed_block = BlockFactory.sign_block(reveal_block, private)
            dag.add_signed_block(block_number, signed_block)            
            block_number += 1

        for i in range(0, Round.PARTIAL_DURATION):
            empty_block = BlockFactory.create_block_dummy(dag.get_top_blocks())
            signed_block = BlockFactory.sign_block(empty_block, private)
            dag.add_signed_block(block_number, signed_block)                        
            block_number += 1

        seed = epoch.calculate_epoch_seed(2)
        self.assertEqual(expected_seed, seed)

    def test_epoch_number(self):
        epoch = Epoch(Dag(0))
        self.assertEqual(epoch.get_epoch_number(6), 1)
        self.assertEqual(epoch.get_epoch_number(7), 2)
        self.assertEqual(epoch.get_epoch_start_block_number(2), 7)
    
    def create_dummy_commit_reveal(era_hash, random_value):
        commit = CommitRandomTransaction()
        encoded, key = encode_value(random_value, era_hash) #todo return random or something
        commit.rand = encoded
        commit.pubkey = os.urandom(128)
        commit.signature = int.from_bytes(os.urandom(128), byteorder='big')

        reveal = RevealRandomTransaction()
        reveal.commit_hash = commit.get_hash().digest()
        reveal.key = b64encode(key.exportKey('DER'))

        return (commit, reveal)

    def create_signed_block_with_tx(transaction):
        block = Block()
        block.prev_hashes = [*self.get_top_blocks()]
        block.timestamp = int(datetime.datetime.now().timestamp())
        block.system_txs = [transaction]
        block_hash = block.get_hash().digest()
        signature = private.sign(block_hash, 0)[0]  #for some reason it returns tuple with second item being None
        signed_block = SignedBlock()
        signed_block.set_block(block)
        signed_block.set_signature(signature)

        return signed_block