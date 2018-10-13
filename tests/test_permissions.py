import unittest

from tools.time import Time
from transaction.gossip_transaction import PenaltyGossipTransaction, \
                                           PositiveGossipTransaction, \
                                           NegativeGossipTransaction
from transaction.stake_transaction import StakeHoldTransaction, StakeReleaseTransaction, PenaltyTransaction
from chain.epoch import Epoch, BLOCK_TIME
from chain.dag import Dag
from chain.block_factory import BlockFactory
from crypto.private import Private
from crypto.keys import Keys
from node.permissions import Permissions
from node.validators import Validators
from tests.test_chain_generator import TestChainGenerator


class TestStakeActions(unittest.TestCase):

    def test_penalty(self):
        dag = Dag(0)
        epoch = Epoch(dag)
        permissions = Permissions(epoch)
        dag.subscribe_to_new_block_notification(epoch)
        node_private = Private.generate()

        initial_validators = Validators.read_genesis_validators_from_file()

        genesis_hash = dag.genesis_block().get_hash()

        last_block_number = Epoch.get_epoch_end_block_number(1)
        prev_hash = TestChainGenerator.fill_with_dummies(dag, genesis_hash, range(1, last_block_number))

        block = BlockFactory.create_block_with_timestamp([prev_hash], BLOCK_TIME * last_block_number)
        tx = PenaltyTransaction()
        tx.conflicts = [prev_hash]
        tx.signature = Private.sign(tx.get_hash(), node_private)
        block.system_txs = [tx]
        signed_block = BlockFactory.sign_block(block, node_private)
        dag.add_signed_block(last_block_number, signed_block)

        initial_validators_order = permissions.get_signers_indexes(genesis_hash)
        # we substract two here: one because it is last but one block
        # and one, because epoch starts from 1
        validator_index_to_penalize = initial_validators_order[last_block_number - 2]

        resulting_validators = permissions.get_validators(block.get_hash())

        self.assertNotEqual(len(initial_validators), len(resulting_validators))
        
        initial_validators.pop(validator_index_to_penalize)

        init_pubkeys = list(map(lambda validator: validator.public_key, initial_validators))
        result_pubkeys = list(map(lambda validator: validator.public_key, resulting_validators))

        self.assertEqual(init_pubkeys, result_pubkeys)

    def test_hold_stake(self):
        dag = Dag(0)
        epoch = Epoch(dag)
        permissions = Permissions(epoch)
        dag.subscribe_to_new_block_notification(epoch)
        node_private = Private.generate()

        initial_validators = Validators.read_genesis_validators_from_file()

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

        tx.pubkey = Private.publickey(node_new_private)
        tx.signature = Private.sign(tx.get_hash(), node_new_private)

        block.system_txs.append(tx)
        signed_block = BlockFactory.sign_block(block, node_private)
        dag.add_signed_block(9, signed_block)

        resulting_validators = permissions.get_validators(block.get_hash())
        pub_keys = []
        for validator in resulting_validators:
            pub_keys.append(validator.public_key)

        self.assertIn(Private.publickey(node_new_private), pub_keys)

    def test_release_stake(self):
        # base initialization
        dag = Dag(0)
        epoch = Epoch(dag)
        permissions = Permissions(epoch)
        dag.subscribe_to_new_block_notification(epoch)
        node_private = Private.generate()

        initial_validators = Validators.read_genesis_validators_from_file()

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
        new_node_public = Private.publickey(new_node_private)

        # create transaction for stake hold for new node
        tx_hold = StakeHoldTransaction()
        tx_hold.amount = 2000
        tx_hold.pubkey = Keys.to_bytes(new_node_public)
        tx_hold.signature = Private.sign(tx_hold.get_hash(), new_node_private)

        # append signed stake hold transaction
        block.system_txs.append(tx_hold)

        # sign block by one of validators
        signed_block = BlockFactory.sign_block(block, node_private)
        # add signed block to DAG
        dag.add_signed_block(9, signed_block)

        resulting_validators = permissions.get_validators(block.get_hash())
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
        tx_release.signature = Private.sign(tx_hold.get_hash(), new_node_private)

        # append signed stake release transaction
        block.system_txs.append(tx_release)

        # sign block by one of validators
        signed_block = BlockFactory.sign_block(block, node_private)
        # add signed block to DAG
        dag.add_signed_block(19, signed_block)

        # verify that new stake holder now is NOT in validators list (after stake release transaction signed by holder)
        resulting_validators = permissions.get_validators(block.get_hash())
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

        initial_validators = Validators.read_genesis_validators_from_file()

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
        tx_release.signature = Private.sign(tx_release.get_hash(), node_private)

        # append signed stake release transaction
        block.system_txs.append(tx_release)

        # sign block by one of validators
        signed_block = BlockFactory.sign_block(block, node_private)
        # add signed block to DAG
        dag.add_signed_block(19, signed_block)

        resulting_validators = permissions.get_validators(block.get_hash())
        pub_keys = []
        for validator in resulting_validators:
            pub_keys.append(validator.public_key)
        self.assertNotIn(genesis_validator.public_key, pub_keys)

    def test_remove_from_validators_by_penalty_gossip(self):
        # base initialization
        dag = Dag(0)
        epoch = Epoch(dag)
        permissions = Permissions(epoch)
        dag.subscribe_to_new_block_notification(epoch)
        node_private = Private.generate()

        initial_validators = Validators.read_genesis_validators_from_file()

        genesis_hash = dag.genesis_block().get_hash()
        prev_hash = genesis_hash
        for i in range(1, 9):
            block = BlockFactory.create_block_with_timestamp([prev_hash], BLOCK_TIME * i)
            signed_block = BlockFactory.sign_block(block, node_private)
            dag.add_signed_block(i, signed_block)
            prev_hash = block.get_hash()

        # get one of validators
        genesis_validator_private = Private.generate()
        genesis_validator_public = initial_validators[9].public_key

        # put to 10 block gossip+ AND gossip- by one node
        block = BlockFactory.create_block_with_timestamp([prev_hash], BLOCK_TIME * 10)

        gossip_negative_tx = NegativeGossipTransaction()
        gossip_negative_tx.pubkey = genesis_validator_public
        gossip_negative_tx.timestamp = Time.get_current_time()
        gossip_negative_tx.number_of_block = 5
        gossip_negative_tx.signature = Private.sign(gossip_negative_tx.get_hash(), genesis_validator_private)
        # create and add to block negative gossip
        block.system_txs.append(gossip_negative_tx)

        gossip_positive_tx = PositiveGossipTransaction()
        gossip_positive_tx.pubkey = genesis_validator_public
        gossip_positive_tx.timestamp = Time.get_current_time()
        gossip_positive_tx.block_hash = dag.blocks_by_number[5][0].get_hash()
        gossip_positive_tx.signature = Private.sign(gossip_positive_tx.get_hash(), genesis_validator_private)
        # create and add to block positive gossip for same number 5 block
        block.system_txs.append(gossip_positive_tx)

        signed_block = BlockFactory.sign_block(block, genesis_validator_private)
        dag.add_signed_block(10, signed_block)
        prev_hash = block.get_hash()
        # --------------------------------------------------

        # put to 11 block penalty gossip
        block = BlockFactory.create_block_with_timestamp([prev_hash], BLOCK_TIME * 11)
        penalty_gossip_tx = PenaltyGossipTransaction()
        penalty_gossip_tx.timestamp = Time.get_current_time()
        penalty_gossip_tx.conflicts = [gossip_positive_tx.get_hash(), gossip_negative_tx.get_hash()]
        # set genesis validator for sign penalty gossip
        penalty_gossip_tx.signature = Private.sign(penalty_gossip_tx.get_hash(), genesis_validator_private)
        block.system_txs.append(penalty_gossip_tx)

        signed_block = BlockFactory.sign_block(block, genesis_validator_private)
        dag.add_signed_block(11, signed_block)
        prev_hash = block.get_hash()
        # --------------------------------------------------

        # verify that genesis node is steel in validators list
        current_epoch_hash = epoch.get_epoch_hashes()
        # for now we DO NOT NEED to recalculate validators (send genesis block hash)
        resulting_validators = permissions.get_validators(current_epoch_hash.get(prev_hash))
        pub_keys = []
        for validator in resulting_validators:
            pub_keys.append(validator.public_key)
        self.assertIn(genesis_validator_public, pub_keys)

        # produce epoch till end
        for i in range(12, 21):
            block = BlockFactory.create_block_with_timestamp([prev_hash], BLOCK_TIME * i)
            signed_block = BlockFactory.sign_block(block, node_private)
            dag.add_signed_block(i, signed_block)
            prev_hash = block.get_hash()

        # check for new epoch
        self.assertTrue(epoch.is_new_epoch_upcoming(i))
        self.assertTrue(epoch.current_epoch == 2)

        # recalculate validators for last block hash
        resulting_validators = permissions.get_validators(prev_hash)
        pub_keys = []
        for validator in resulting_validators:
            pub_keys.append(validator.public_key)

        self.assertNotIn(genesis_validator_public, pub_keys)


