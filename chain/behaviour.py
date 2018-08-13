class Behaviour():
    def __init__(self):
        self.malicious_excessive_block = False
        self.malicious_skip_block = False
        self.wants_to_hold_stake = False
        self.wants_to_release_stake = False

    def is_malicious_excessive_block(self):
        return self.malicious_excessive_block

    def is_malicious_skip_block(self):
        return self.malicious_skip_block

    def should_hold_stake(self):
        return self.wants_to_hold_stake
    
    def should_release_stake(self):
        return self.wants_to_release_stake