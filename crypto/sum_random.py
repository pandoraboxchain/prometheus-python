from Crypto.Hash import SHA256
import random

def sum_random(random_list):
    res = random_list[0]
    for item in random_list[1:]:
        num = item
        res = num ^ res
    return res

#sum_random([SHA256.new(b"324a"),SHA256.new(b"3s24a"), SHA256.new(b"3s24a")])

# def calculate_validators_indexes(seed, validators_count, epoch_size):
#     current = seed.to_bytes(32, byteorder='big')
#     res = []
#     for n in range(epoch_size):
#         lr = int.from_bytes(current, byteorder='big')            
#         res.append(lr % validators_count)
#         current = SHA256.new(current).digest()
#     return res

def calculate_validators_indexes(seed, validators_count, epoch_size):
    random.seed(seed)
    validators_list = []
    for i in range(0,validators_count):
        validators_list.append(i)
    sattolo_cycle(validators_list)
    return validators_list

# array shuffling method straight from the wikipedia
def sattolo_cycle(items):
    i = len(items)
    while i > 1:
        i = i - 1
        j = random.randrange(i)  # 0 <= j <= i-1
        items[j], items[i] = items[i], items[j]
