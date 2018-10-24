from chain.block import Block
from chain.transaction_factory import TransactionFactory

class Genesis(Block):
    def __init__(self, creation_time):
        self.timestamp = creation_time
        self.prev_hashes = []
        self.system_txs = []
        self.payment_txs = []

        self.precalculated_genesis_hash = Block.get_hash(self)
    
    def get_hash(self):
        return self.precalculated_genesis_hash
        


