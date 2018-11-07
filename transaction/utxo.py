from transaction.payment_transaction import PaymentTransaction

COINBASE_IDENTIFIER = b'0' * 32

class Utxo:
    def __init__(self, logger=None):
        self.utxo = {}
        self.logger = logger
    
    def add(self, tx):
        
        if tx.input != COINBASE_IDENTIFIER: # do not decrease any values if it is coinbase tx
            assert tx.input in self.utxo
            input_value = self.utxo[tx.input][tx.number]
            total_amount = sum(tx.amounts)
            input_value -= total_amount
            assert input_value >= 0
            if input_value == 0:
                del self.utxo[tx.input][tx.number]
            if not self.utxo[tx.input]:
                del self.utxo[tx.input]
        
        tx_hash = tx.get_hash()
        if tx_hash in self.utxo:
            if self.logger:
                self.logger.info("Overwriting unspent output with hash with hash %s", tx_hash)
        self.utxo[tx_hash] = {}
        for i in range(len(tx.outputs)):
            self.utxo[tx_hash][i] = tx.amounts[i]
    
    def apply_payments(self, payments):
        return #turn off UTXO temporarily, as it is badly reacting to conflicts
        for payment in payments:
            self.add(payment)
