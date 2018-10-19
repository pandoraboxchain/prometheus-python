from node.genesis_validators import GenesisValidators


class BlockSigner:

    def __init__(self, private_key):
        self.private_key = private_key

    def set_private_key(self, private_key):
        self.private_key = private_key


class BlockSigners:

    def __init__(self):
        self.block_signers = []
        self.get_from_file()

    def get_from_file(self):
        for key in GenesisValidators.private_keys:
            block_signer = BlockSigner(key)
            self.block_signers.append(block_signer)
