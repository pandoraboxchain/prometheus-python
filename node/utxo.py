from transaction.payment_transaction import PaymentTransaction

COINBASE_IDENTIFIER = b'0' * 32

class Utxo:
    def __init__(self):
        self.txs = {}
    
    def add(self, tx):
        
        if tx.input != COINBASE_IDENTIFIER: # do not decrease any values if it is coinbase tx
            assert tx.input in self.txs
            input_value = self.txs[tx.input][tx.number]
            total_amount = sum(tx.amounts)
            input_value -= total_amount
            assert input_value >= 0
            if input_value == 0:
                del self.txs[tx.input][tx.number]
        
        tx_hash = tx.get_hash()
        assert tx_hash not in self.txs
        self.txs[tx_hash] = {}
        for i in range(len(tx.outputs)):
            self.txs[tx_hash][i] = tx.amounts[i]
    
    def apply_payments(self, payments):
        for payment in payments:
            self.add(payment)
