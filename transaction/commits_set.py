from chain.block import Block
from transaction.transaction import CommitRandomTransaction, RevealRandomTransaction
from crypto.dec_part_random import dec_part_random

class CommitsSet:
    def __init__(self, epoch, epoch_number, top_block_hash):
        self.transactions_by_hash = {}
        self.transactions_by_pubkey = {}
        self.collect_commited_transactions(epoch, epoch_number, top_block_hash)

    def collect_commited_transactions(self, epoch, epoch_number, block_hash):
        blocks = epoch.backwards_collect_commit_blocks_for_epoch(epoch_number, block_hash)
        
        for block in blocks:
            if hasattr(block, "system_txs"):
                for tx in block.system_txs:
                    if isinstance(tx, CommitRandomTransaction):
                        self.add_transaction(tx)
        

    def add_transaction(self, tx):
        tx_hash = tx.get_hash().digest()
        self.transactions_by_hash[tx_hash] = tx

        pubkey = tx.pubkey
        self.transactions_by_pubkey[pubkey] = tx

