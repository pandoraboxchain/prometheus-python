from Crypto.Hash import SHA256

def sum_random(random_list):
    res = random_list[0]
    for item in random_list[1:]:
        res = [a^b for a,b in zip(item,res)]
    return res

#sum_random([SHA256.new(b"324a").digest(),SHA256.new(b"3s24a").digest(), SHA256.new(b"3s24a").digest()])

def get_random(random_list, validators_count, era_size):
    sr = bytes(sum_random(random_list))
    current = sr
    res = []
    for n in range(era_size):
        lr = 0
        for b in current:
            lr *= 256
            lr += b
        res.append(lr % validators_count)
        current = SHA256.new(current).digest()
    return res
