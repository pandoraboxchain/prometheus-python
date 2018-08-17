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
        dag.add_signed_block(i, signed_block)

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


    def test_release_stake(self):
        # base initialization
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

        # create new node for stake hold
        new_node_private = Private.generate()
        new_node_public = new_node_private.publickey()

        # create transaction for stake hold for new node
        tx_hold = StakeHoldTransaction()
        tx_hold.amount = 2000
        tx_hold.pubkey = Keys.to_bytes(new_node_public)
        tx_hold.signature = new_node_private.sign(tx_hold.get_hash(), 0)[0]

        # append signed stake hold transaction
        block.system_txs.append(tx_hold)

        # sign block by one of validators
        signed_block = BlockFactory.sign_block(block, node_private)
        # add signed block to DAG
        dag.add_signed_block(9, signed_block)

        # verify that new stake holder now is in validators list
        resulting_validators = permissions.get_validators_for_epoch_hash(block.get_hash())
        pub_keys = []
        for validator in resulting_validators:
            pub_keys.append(validator.public_key)
        self.assertIn(new_node_public, pub_keys)

        # add blocks for new epoch
        for i in range(10, 18):
            block = BlockFactory.create_block_with_timestamp([prev_hash], BLOCK_TIME * i)
            signed_block = BlockFactory.sign_block(block, node_private)
            dag.add_signed_block(i, signed_block)
            prev_hash = block.get_hash()

        # create stake release transaction for new stakeholder
        tx_release = StakeReleaseTransaction()
        tx_release.pubkey = Keys.to_bytes(new_node_public)
        tx_release.signature = new_node_private.sign(tx_hold.get_hash(), 0)[0]

        # append signed stake release transaction
        block.system_txs.append(tx_release)

        # sign block by one of validators
        signed_block = BlockFactory.sign_block(block, node_private)
        # add signed block to DAG
        dag.add_signed_block(19, signed_block)

        # verify that new stake holder now is NOT in validators list (after stake release transaction signed by holder)
        resulting_validators = permissions.get_validators_for_epoch_hash(block.get_hash())
        pub_keys = []
        for validator in resulting_validators:
            pub_keys.append(validator.public_key)
        self.assertNotIn(new_node_public, pub_keys)


    def test_stake_release_by_genesis_validator(self):
        # base initialization
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

        # get one of validators
        genesis_validator = initial_validators[9]

        # create stake release transaction for new stakeholder
        tx_release = StakeReleaseTransaction()
        tx_release.pubkey = Keys.to_bytes(genesis_validator.public_key)
        tx_release.signature = node_private.sign(tx_release.get_hash(), 0)[0]

        # append signed stake release transaction
        block.system_txs.append(tx_release)

        # sign block by one of validators
        signed_block = BlockFactory.sign_block(block, node_private)
        # add signed block to DAG
        dag.add_signed_block(19, signed_block)

        # verify that validator release stake
        resulting_validators = permissions.get_validators_for_epoch_hash(block.get_hash())
        pub_keys = []
        for validator in resulting_validators:
            pub_keys.append(validator.public_key)
        self.assertNotIn(genesis_validator.public_key, pub_keys)

