import random


def sum_random(random_list):
    res = random_list[0]
    for item in random_list[1:]:
        num = item
        res = num ^ res
    return res


def calculate_validators_indexes(seed, validators_count):
    random.seed(seed)
    validators_list = []
    for i in range(0,validators_count):
        validators_list.append(i)
    sattolo_cycle(validators_list)
    return validators_list


# array shuffling method straight from the wikipedia
# it is sufficient for now, but it always removes number from its position
# i.e. zero never be at index 0, two won't be at index 0
def sattolo_cycle(items):
    i = len(items)
    while i > 1:
        i = i - 1
        j = random.randrange(i)  # 0 <= j <= i-1
        items[j], items[i] = items[i], items[j]
