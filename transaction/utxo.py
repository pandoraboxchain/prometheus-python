from chain.block import Block
from transaction.transaction import CommitRandomTransaction, RevealRandomTransaction
from crypto.dec_part_random import dec_part_random

class Utxo:
    
    commited_transactions = {}
    revealed_randoms = []

    def get_commited_transaction_by_hash(self, tx_hash):
        return self.commited_transactions[tx_hash]

    def add_transaction(self, tx):
        tx_hash = tx.get_hash().digest()
        self.commited_transactions[tx_hash] = tx

    def handle_new_block(self, block):
        for tx in block.system_txs:
            if isinstance(tx, CommitRandomTransaction):
                self.add_transaction(tx)
            elif isinstance(tx, RevealRandomTransaction):
                commit = self.commited_transactions[tx.commited_hash]
                result = dec_part_random(commit.rand, tx.key)
                if result:
                    self.revealed_randoms.append(result)
                    del self.commited_transactions[tx.commited_hash]


