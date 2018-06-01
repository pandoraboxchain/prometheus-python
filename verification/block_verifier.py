from Crypto.Hash import SHA256
import struct
from transaction.transaction import CommitRandomTransaction, RevealRandomTransaction
from crypto.dec_part_random import dec_part_random

class BlockVerifier():
    def check_if_valid(block, commits_set):
        for tx in block.system_txs:
            if isinstance(tx, CommitRandomTransaction):
                if tx.pubkey in commits_set.transactions_by_pubkey:
                    return False
                return True
            if isinstance(tx, RevealRandomTransaction):
                if not tx.commit_hash in commits_set.transaction_by_hash:
                    return False
                commit = commits_set[tx.commit_hash]
                result = dec_part_random(commit.rand, tx.key)
                if result: #TODO make sure this check is meaningful
                    return True
                else:
                    return False
        return True
