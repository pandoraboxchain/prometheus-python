

class ConflictWatcher:
    def __init__(self, dag):
        self.dag = dag
        self.pubkeys_by_epochs = []  # epoch number : public_key : block hashes list
        self.blocks = {}  # block hash : (public key, epoch_number)

    def on_new_block_by_validator(self, block_hash, epoch_number, public_key):
        self.blocks[block_hash] = (public_key, epoch_number)
        if not epoch_number in self.pubkeys_by_epochs:
            self.pubkeys_by_epochs[epoch_number] = {public_key : [block_hash]}
        else:
            self.pubkeys_by_epochs[epoch_number][public_key].append(block_hash)

    def get_conflicts_by_block(self, block_hash):
        pubkey, epoch_number = self.blocks[block_hash]
        return self.get_conflicts_by_pubkey(pubkey, epoch_number)

    def get_conflicts_by_pubkey(self, pubkey, epoch_number):
        conflicts = self.pubkeys_by_epochs[epoch_number][pubkey]
        if len(conflicts) == 1:
            return None
        return conflicts
        
