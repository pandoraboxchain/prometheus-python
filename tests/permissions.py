import unittest
import os
from chain.block import Block
from transaction.stake_transaction import StakeHoldTransaction, StakeReleaseTransaction, PenaltyTransaction
from chain.epoch import Epoch, BLOCK_TIME
from chain.dag import Dag
from chain.permissions import Permissions
from crypto.private import Private
from crypto.keys import Keys
from chain.block_factory import BlockFactory
from chain.validators import Validators

from Crypto.Hash import SHA256

class TestStakeActions(unittest.TestCase):

    def test_penalty(self):
        dag = Dag(0)
        epoch = Epoch(dag)
        permissions = Permissions(epoch)
        dag.subscribe_to_new_block_notification(epoch)
        node_private = Private.generate()

        initial_validators = Validators().validators

        genesis_hash = dag.genesis_block().get_hash()
        prev_hash = genesis_hash
        print("genesis hash", prev_hash.hex())
        for i in range(1, 9):
            block = BlockFactory.create_block_with_timestamp([prev_hash], BLOCK_TIME * i)
            signed_block = BlockFactory.sign_block(block, node_private)
            dag.add_signed_block(i, signed_block)
            prev_hash = block.get_hash()
            print("prev hash", prev_hash.hex())

        block = BlockFactory.create_block_with_timestamp([prev_hash], BLOCK_TIME * 9)
        tx = PenaltyTransaction()
        tx.conflicts = [prev_hash]
        tx.signature = node_private.sign(tx.get_hash(), 0)[0]

        block.system_txs = [tx]
        signed_block = BlockFactory.sign_block(block, node_private)
        dag.add_signed_block(i, signed_block)

        initial_validators.pop(0)

        resulting_validators = permissions.get_validators_for_epoch_hash(block.get_hash())

        self.assertEqual(len(initial_validators), len(resulting_validators))
        for i in range(len(initial_validators)):
            self.assertEqual(initial_validators[i].public_key, resulting_validators[i].public_key)
        
