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
from visualization.dag_visualizer import DagVisualizer


class TestStakeActions(unittest.TestCase):

    @unittest.skip('penalty gossip tx implementation')
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

        # TODO why we send block.get_hash() while we need current epoch hash ?
        # for wrong epoch hash all current validators list will be recalculated
        # block.het_hash() != epoch.get_hash()
        resulting_validators = permissions.get_validators(block.get_hash())

        self.assertNotEqual(len(initial_validators), len(resulting_validators))
        
        initial_validators.pop(validator_index_to_penalize)

        init_pubkeys = list(map(lambda validator: validator.public_key, initial_validators))
        result_pubkeys = list(map(lambda validator: validator.public_key, resulting_validators))

        self.assertEqual(init_pubkeys, result_pubkeys)

    @unittest.skip('penalty gossip tx implementation')
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

    @unittest.skip('penalty gossip tx implementation')
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

        # verify that new stake holder now is in validators list
        # TODO why we send block.get_hash() while we need current epoch hash ?
        # for wrong epoch hash all current validators list will be recalculated
        # block.het_hash() != epoch.get_hash()
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

    @unittest.skip('penalty gossip tx implementation')
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

        # verify that validator release stake
        # TODO why we send block.get_hash() while we need current epoch hash ?
        # for wrong epoch hash all current validators list will be recalculated
        # block.het_hash() != epoch.get_hash()
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

        # ------------------------------------------------
        # provide stake hold tx for become stakeholder
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
        prev_hash = block.get_hash()

        # verify that new stake holder now is in validators list
        resulting_validators = permissions.get_validators(prev_hash)
        # -------------------------------------------------

        # get stakeholder validators (for now new node not added to validators list)
        pub_keys = []
        for validator in resulting_validators:
            pub_keys.append(validator.public_key)
        self.assertNotIn(new_node_public, pub_keys)

        block = BlockFactory.create_block_with_timestamp([prev_hash], BLOCK_TIME * 10)
        # create penalty gossip transaction for stakeholder
        # --------------------------------------------------
        # private = Private.generate()

        # modeling different combination of conflict
        # --------------------------------------------------
        # malicious validator (must be excluded from validators list on next epoch)
        gossip_negative_tx = NegativeGossipTransaction()
        gossip_negative_tx.pubkey = new_node_public
        gossip_negative_tx.timestamp = Time.get_current_time()
        gossip_negative_tx.number_of_block = 5
        gossip_negative_tx.signature = Private.sign(gossip_negative_tx.get_hash(), new_node_private)
        # create and add to block negative gossip
        block.system_txs.append(gossip_negative_tx)

        gossip_positive_tx = PositiveGossipTransaction()
        gossip_positive_tx.pubkey = new_node_public
        gossip_positive_tx.timestamp = Time.get_current_time()
        gossip_positive_tx.block_hash = dag.blocks_by_number[5][0].get_hash()
        gossip_positive_tx.signature = Private.sign(gossip_positive_tx.get_hash(), new_node_private)
        # create and add to block positive gossip for same number 5 block
        block.system_txs.append(gossip_positive_tx)
        # --------------------------------------------------

        penalty_gossip_tx = PenaltyGossipTransaction()
        penalty_gossip_tx.timestamp = Time.get_current_time()
        penalty_gossip_tx.conflicts = [gossip_positive_tx.get_hash(), gossip_negative_tx.get_hash()]
        # set genesis validator for sign penalty gossip
        penalty_gossip_tx.signature = Private.sign(penalty_gossip_tx.get_hash(), new_node_private)
        # --------------------------------------------------

        # append signed stake release transaction
        block.system_txs.append(penalty_gossip_tx)
        prev_hash = block.get_hash()

        # sign block by one of validators
        signed_block = BlockFactory.sign_block(block, new_node_private)
        # add signed block to DAG
        dag.add_signed_block(10, signed_block)

        # verify that new node (which will be penaltize on next epoch) still not in validators list of current epoch
        resulting_validators = permissions.get_validators(signed_block.get_hash())
        pub_keys = []
        for validator in resulting_validators:
            pub_keys.append(validator.public_key)
        self.assertNotIn(new_node_public, pub_keys)

        # produce epoch till end
        for i in range(11, 21):
            block = BlockFactory.create_block_with_timestamp([prev_hash], BLOCK_TIME * i)
            signed_block = BlockFactory.sign_block(block, node_private)
            dag.add_signed_block(i, signed_block)
            prev_hash = block.get_hash()
            epoch.is_new_epoch_upcoming(i)  # epoch wount change if not call this method

        # show DAG
        # DagVisualizer.visualize(dag)
        current_epoch = epoch.current_epoch
        current_epoch_hash = prev_hash #maybe
        # for now its HOLD stake and than release by penalty gossip
        resulting_validators = permissions.get_validators(current_epoch_hash)  # recalculating validators on new epch
        pub_keys = []
        for validator in resulting_validators:
            pub_keys.append(validator.public_key)

        self.assertNotIn(new_node_public, pub_keys)


