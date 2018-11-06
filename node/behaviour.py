class Behaviour:
    def __init__(self):
        self.malicious_excessive_block = False
        self.malicious_skip_block = False
        self.malicious_wrong_signature = False
        self.malicious_wrong_signature_epoch = False
        self.wants_to_hold_stake = False
        self.wants_to_release_stake = False
        self.epoch_to_release_stake = -1

        self.malicious_send_negative_gossip_count = -1
        self.malicious_send_positive_gossip_count = -1

        # behavior flag for create block but not broadcast it
        # added as temporary fast solution
        self.transport_cancel_block_broadcast = False
        # behavior flag for emulation node in offline for input and output requests
        self.transport_node_disable_input = False
        self.transport_node_disable_output = False
        self.transport_keep_offline = []

        # Malicious blocks (validated by block_verifier)
        self.malicious_private_transactions_in_block = False
        self.malicious_timeslot_of_block = False
        self.malicious_block_dont_add_system_transactions = False

        # Malicious transactions (validated by transaction_verifier)
        self.malicious_transaction_broadcasting_private_key = False
        self.malicious_transaction_broadcasting_penalty = False

        self.malicious_public_key_transaction = False

        self.malicious_transaction_wrong_sender_for_current_round = False
        self.malicious_transaction_generate_too_few_secret_shares = False
        self.malicious_transaction_send_reveal_without_corresponding_commit = False

        flags = dir(self)
        self.flags_of_malice = [flag for flag in flags if flag.startswith("malicious")]

    def update(self, epoch_number):
        if self.epoch_to_release_stake == epoch_number:
            self.wants_to_release_stake = True
            self.epoch_to_release_stake = -1

    def update_transport(self, current_block_number):
        if len(self.transport_keep_offline) == 2:
            if current_block_number in range(self.transport_keep_offline[0], self.transport_keep_offline[1] + 1):
                self.transport_node_disable_input = True
                self.transport_node_disable_output = True
            else:
                self.transport_node_disable_input = False
                self.transport_node_disable_output = False

    def is_malicious_excessive_block(self):
        return self.malicious_excessive_block

    def is_malicious_skip_block(self):
        return self.malicious_skip_block

    def should_hold_stake(self):
        return self.wants_to_hold_stake
    
    def should_release_stake(self):
        return self.wants_to_release_stake

    def get_malicious_flags_names(self):
        return self.flags_of_malice
