import unittest
from chain.block import Block
from transaction.transaction import CommitRandomTransaction, RevealRandomTransaction
from transaction.utxo import Utxo
from crypto.enc_random import enc_part_random

class TestUtxo(unittest.TestCase):

    def test_commit_reveal(self):
        utxo = Utxo()
        
        commit = CommitRandomTransaction()
        data, key = enc_part_random(b'era_hash')
        commit.rand = data
        commit.pubkey = b'123456789'
        commit_block = Block()
        commit_block.system_txs = [commit]

        utxo.handle_new_block(commit_block);
        self.assertEqual(len(utxo.commited_transactions), 1)

        reveal = RevealRandomTransaction()
        reveal.commited_hash = commit.get_hash().digest()
        reveal.key = key

        reveal_block = Block()
        reveal_block.system_txs = [reveal]

        utxo.handle_new_block(reveal_block);        
        self.assertEqual(len(utxo.commited_transactions), 0)
        self.assertEqual(len(utxo.revealed_randoms), 1)