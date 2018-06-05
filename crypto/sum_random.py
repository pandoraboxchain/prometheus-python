from Crypto.Hash import SHA256

def sum_random(random_list):
    res = random_list[0]
    for item in random_list[1:]:
        num = item
        res = num ^ res
    return res

#sum_random([SHA256.new(b"324a").digest(),SHA256.new(b"3s24a").digest(), SHA256.new(b"3s24a").digest()])

def calculate_validators_numbers(seed, validators_count, epoch_size):
    current = seed.to_bytes(32, byteorder='big')
    res = []
    for n in range(epoch_size):
        lr = int.from_bytes(current, byteorder='big')            
        res.append(lr % validators_count)
        current = SHA256.new(current).digest()
    return res
