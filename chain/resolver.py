class Entry():
    def __init__(self, tx, number):
        self.tx = tx
        self.number = number
    
    def __eq__(self, other):
        return self.tx == other.tx and self.number == other.number

class Resolver:
    @staticmethod
    def resolve(ordered_payment_lists):
        spent = []
        unspent = []
        internally_spent = [] #this list is append only
        for payment_list in ordered_payment_lists:
            for payment in payment_list:
                entry = Entry(payment.input, payment.number)
                if entry in spent or entry in internally_spent:
                    continue # transaction conflict: already spent
                if entry in unspent:
                    internally_spent.append(entry)
                    unspent.remove(entry)
                else:
                    spent.append(entry)
                
                for i in range(len(payment.outputs)):
                    unspent.append(Entry(payment.get_hash(), i))
        
        return spent, unspent


                
                    
    
