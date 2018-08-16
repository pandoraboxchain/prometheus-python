import unittest

from crypto.keys import Keys
from transaction.stake_transaction import PenaltyTransaction, StakeHoldTransaction, StakeReleaseTransaction
from chain.epoch import Epoch, BLOCK_TIME
from chain.dag import Dag
from chain.permissions import Permissions
from crypto.private import Private
from chain.block_factory import BlockFactory
from chain.validators import Validators


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
        for i in range(1, 9):
            block = BlockFactory.create_block_with_timestamp([prev_hash], BLOCK_TIME * i)
            signed_block = BlockFactory.sign_block(block, node_private)
            dag.add_signed_block(i, signed_block)
            prev_hash = block.get_hash()

        block = BlockFactory.create_block_with_timestamp([prev_hash], BLOCK_TIME * 9)
        tx = PenaltyTransaction()
        tx.conflicts = [prev_hash]
        tx.signature = node_private.sign(tx.get_hash(), 0)[0]

        block.system_txs = [tx]
        signed_block = BlockFactory.sign_block(block, node_private)
        dag.add_signed_block(9, signed_block)

        initial_validators.pop(0)

        resulting_validators = permissions.get_validators_for_epoch_hash(block.get_hash())

        self.assertEqual(len(initial_validators), len(resulting_validators))
        for i in range(len(initial_validators)):
            self.assertEqual(initial_validators[i].public_key, resulting_validators[i].public_key)

    def test_hold_stake(self):
        dag = Dag(0)
        epoch = Epoch(dag)
        permissions = Permissions(epoch)
        dag.subscribe_to_new_block_notification(epoch)
        node_private = Private.generate()

        initial_validators = Validators().validators

        genesis_hash = dag.genesis_block().get_hash()
        prev_hash = genesis_hash
        for i in range(1, 9):
            block = BlockFactory.create_block_with_timestamp([prev_hash], BLOCK_TIME * i)
            signed_block = BlockFactory.sign_block(block, node_private)
            dag.add_signed_block(i, signed_block)
            prev_hash = block.get_hash()

        block = BlockFactory.create_block_with_timestamp([prev_hash], BLOCK_TIME * 9)

        tx = StakeHoldTransaction()
        tx.amount = 1000
        node_new_private = Private.generate()

        tx.pubkey = Keys.to_bytes(node_new_private.publickey())
        tx.signature = node_new_private.sign(tx.get_hash(), 0)[0]

        block.system_txs.append(tx)
        signed_block = BlockFactory.sign_block(block, node_private)
        dag.add_signed_block(9, signed_block)

        resulting_validators = permissions.get_validators_for_epoch_hash(block.get_hash())
        pub_keys = []
        for validator in resulting_validators:
            pub_keys.append(validator.public_key)

        self.assertIn(node_new_private.publickey(), pub_keys)

