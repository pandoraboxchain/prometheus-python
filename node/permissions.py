from chain.epoch import Epoch
from chain.params import Round
from transaction.gossip_transaction import PenaltyGossipTransaction
from transaction.stake_transaction import StakeHoldTransaction, PenaltyTransaction, StakeReleaseTransaction
from node.validators import Validator, Validators
from node.stake_manager import StakeManager
from crypto.keys import Keys
from crypto.entropy import Source
from chain.params import SECRET_SHARE_PARTICIPANTS_COUNT


class Permissions:

    def __init__(self, epoch, validators=Validators()):
        initial_validators = validators.validators
        if not initial_validators:
            initial_validators = Validators.read_genesis_validators_from_file()
        self.epoch = epoch
        self.stake_manager = StakeManager(epoch)
        genesis_hash = self.epoch.dag.genesis_block().get_hash()
        validator_count = len(initial_validators)
        initial_signers_indexes = validators.signers_order
        if not initial_signers_indexes:
            initial_signers_indexes = self.epoch.calculate_validators_indexes(genesis_hash, validator_count, Source.SIGNERS)

        initial_randomizers_indexes = validators.randomizers_order
        if not initial_randomizers_indexes:
            initial_randomizers_indexes = self.epoch.calculate_validators_indexes(genesis_hash, validator_count, Source.RANDOMIZERS)

        self.log("Initial signers:", initial_signers_indexes[0:3], initial_signers_indexes[3:6], initial_signers_indexes[6:9], initial_signers_indexes[9:12], initial_signers_indexes[12:15], initial_signers_indexes[15:19])
        self.log("Initial randomizers:", initial_randomizers_indexes)

        # init validators list and indexes, so we can build list of future validators based on this
        self.epoch_validators = { genesis_hash : initial_validators }
        self.signers_indexes = { genesis_hash : initial_signers_indexes }
        self.randomizers_indexes = { genesis_hash : initial_randomizers_indexes }

    def get_sign_permission(self, epoch_hash, block_number_in_epoch):
        validators_for_epoch = self.get_validators(epoch_hash)
        random_signers_indexes = self.get_signers_indexes(epoch_hash)
        # cycle validators in case of exclusion
        if block_number_in_epoch >= len(validators_for_epoch):
            block_number_in_epoch = block_number_in_epoch % len(validators_for_epoch)
            print("Looping epoch validators. Next block validator is as in block number", block_number_in_epoch)
        index = random_signers_indexes[block_number_in_epoch]
        return validators_for_epoch[index]

    def get_commiters(self, epoch_hash):
        validators_for_epoch = self.get_validators(epoch_hash)
        random_indexes = self.get_randomizers_indexes(epoch_hash)
        sharers = []
        for index in random_indexes[:SECRET_SHARE_PARTICIPANTS_COUNT]:
            sharers.append(validators_for_epoch[index])
        return sharers

    def get_commiters_pubkeys(self, epoch_hash):
        return [commiter.public_key for commiter in self.get_commiters(epoch_hash)]

    def get_secret_sharers(self, epoch_hash):
        validators_for_epoch = self.get_validators(epoch_hash)
        random_indexes = self.get_randomizers_indexes(epoch_hash)
        sharers = []
        for index in random_indexes[-SECRET_SHARE_PARTICIPANTS_COUNT:]:
            sharers.append(validators_for_epoch[index])
        return sharers

    def get_secret_sharers_pubkeys(self, epoch_hash):
        return [secret_sharer.public_key for secret_sharer in self.get_secret_sharers(epoch_hash)]

    def get_signers_indexes(self, epoch_hash):
        if not epoch_hash in self.signers_indexes:
            epoch_validators = self.get_validators(epoch_hash)
            self.log("Total signers count", len(epoch_validators))
            random_indexes = self.epoch.calculate_validators_indexes(epoch_hash, len(epoch_validators), Source.SIGNERS)
            self.log("Calculated signers:", random_indexes[0:3], random_indexes[3:6], random_indexes[6:9], random_indexes[9:12], random_indexes[12:15], random_indexes[15:19])
            self.signers_indexes[epoch_hash] = random_indexes
        return self.signers_indexes[epoch_hash]

    def get_randomizers_indexes(self, epoch_hash):
        if not epoch_hash in self.randomizers_indexes:
            epoch_validators = self.get_validators(epoch_hash)
            self.log("Total randomizers count", len(epoch_validators))
            random_indexes = self.epoch.calculate_validators_indexes(epoch_hash, len(epoch_validators), Source.RANDOMIZERS)
            self.log("Calculated randomizers:", random_indexes)
            self.randomizers_indexes[epoch_hash] = random_indexes
        return self.randomizers_indexes[epoch_hash]

    def get_validators(self, epoch_hash):
        if epoch_hash not in self.epoch_validators:
            self.calculate_validators_for_epoch(epoch_hash)
        return self.epoch_validators[epoch_hash]

    def calculate_validators_for_epoch(self, epoch_hash):
        prev_epoch_hash = self.epoch.get_previous_epoch_hash(epoch_hash)
        validators = self.get_validators(prev_epoch_hash)
        stake_actions = self.stake_manager.get_stake_actions(epoch_hash)
        validators = self.apply_stake_actions(validators, stake_actions)
        self.epoch_validators[epoch_hash] = validators

    def get_ordered_signers_pubkeys_for_round(self, epoch_hash, round_type):
        selected_epoch_validators = self.get_validators(epoch_hash)

        epoch_signers_indexes = self.get_signers_indexes(epoch_hash)
        validators = []	
        for i in Epoch.get_round_range(1, round_type):	
            index = epoch_signers_indexes[i-1]
            validators.append(selected_epoch_validators[index])

        return validators

    def get_ordered_randomizers_pubkeys_for_round(self, epoch_hash, round_type):
        selected_epoch_validators = self.get_validators(epoch_hash)

        epoch_random_indexes = []
        if round_type==Round.PUBLIC or round_type==Round.PRIVATE:
            epoch_random_indexes = self.get_signers_indexes(epoch_hash)
            round_type=Round.PRIVATE

            validators = []	
            for i in Epoch.get_round_range(1, round_type):	
                index = epoch_random_indexes[i-1]
                validators.append(selected_epoch_validators[index])

            return validators

        elif round_type==Round.SECRETSHARE:
            return self.get_secret_sharers(epoch_hash)
        elif round_type==Round.COMMIT or round_type==Round.REVEAL:
            return self.get_commiters(epoch_hash)   

        assert False, "No randomizers exist for this round type!"

    def get_random_senders_pubkeys(self, epoch_hash):
        selected_epoch_validators = self.get_validators(epoch_hash)
        epoch_random_indexes = self.get_randomizers_indexes(epoch_hash)
        validators = []	
        for i in Epoch.get_round_range(1, Round.SECRETSHARE):	
            index = epoch_random_indexes[i-1]
            validators.append(selected_epoch_validators[index])

        return validators
    
    def get_block_validator(self, block_hash):
        block_number = self.epoch.dag.get_block_number(block_hash)
        epoch_block_number = self.epoch.convert_to_epoch_block_number(block_number)
        epoch_hash = self.epoch.find_epoch_hash_for_block(block_hash)
        assert epoch_hash, "Can't find epoch hash for block"
        return self.get_sign_permission(epoch_hash, epoch_block_number)

    # TODO (incorrect)
    def get_tx_by_hash(self, tx_hash):
        for i in self.epoch.dag.blocks_by_number:
            signed_block = self.epoch.dag.blocks_by_number[i]
            block = signed_block[0].block
            if len(block.system_txs) > 0:
                for tx in block.system_txs:
                    if tx_hash == tx.get_hash():
                        return tx  # return tx by hash searching
        assert tx, "Cant find tx by hash"

    # this method modifies list, but also returns it for API consistency
    def apply_stake_actions(self, validators, actions):
        for action in actions:
            if isinstance(action, PenaltyTransaction):
                for conflict in action.conflicts:
                    culprit = self.get_block_validator(conflict)
                    self.release_stake(validators, Keys.to_bytes(culprit.public_key))
            elif isinstance(action, PenaltyGossipTransaction):
                # in one conflict we have [positive_gossip_tx_hash, negative_gossip_tx_hash]
                # TODO incorrect (move to ----> BlockAcceptor)
                positive_gossip = self.get_tx_by_hash(action.conflicts[0])  # positive gossip tx
                negative_gossip = self.get_tx_by_hash(action.conflicts[1])  # negative gossip tx
                if (positive_gossip.pubkey == negative_gossip.pubkey) and \
                        (negative_gossip.number_of_block == self.epoch.dag.get_block_number(positive_gossip.block_hash)):
                    culprit = negative_gossip.pubkey
                    self.release_stake(validators, Keys.to_bytes(culprit))

            elif isinstance(action, StakeHoldTransaction):
                self.hold_stake(validators, action.pubkey, action.amount)
            elif isinstance(action, StakeReleaseTransaction):
                self.release_stake(validators, action.pubkey)
        return validators

    @staticmethod
    def hold_stake(validators, pubkey, stake):
        validators.append(Validator(Keys.from_bytes(pubkey), stake))

    @staticmethod
    def release_stake(validators, pubkey):
        for i in range(len(validators)):
            if validators[i].public_key == Keys.from_bytes(pubkey):
                del validators[i]
                break

    @staticmethod
    def sort_by_stake(validators):
        return sorted(validators, key=attrgetter("stake"), reverse=True)

    # ¯\_( )_/¯
    def log(self, *args):
        self.epoch.log(args)

