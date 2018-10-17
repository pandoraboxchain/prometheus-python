import random
from chain.block import Block
from chain.signed_block import SignedBlock
from transaction.gossip_transaction import NegativeGossipTransaction, PositiveGossipTransaction, \
    PenaltyGossipTransaction


class Dag:
    
    def __init__(self, genesis_creation_time):
        self.genesis_creation_time = genesis_creation_time
        self.blocks_by_hash = {}  # just hash map hash:block
        self.blocks_by_number = {}  # key is timeslot number, value is a list of blocks in this timeslot
        self.transactions_by_hash = {}  # key is tx_hash, value is tx
        self.existing_links = []
        self.tops = {}
        self.new_block_listeners = []
        signed_genesis_block = SignedBlock()
        signed_genesis_block.set_block(self.genesis_block())
        self.add_signed_block(0, signed_genesis_block)

    def genesis_block(self):
        block = Block()
        block.timestamp = self.genesis_creation_time
        block.prev_hashes = []
        return block

    # ------------------------------
    # block methods
    # ------------------------------
    def add_signed_block(self, index, block):
        block_hash = block.block.get_hash()
        if block_hash in self.blocks_by_hash:
            assert False, "Trying to add block with the hash which already exists"
        self.blocks_by_hash[block_hash] = block
        if index in self.blocks_by_number:
            self.blocks_by_number[index].append(block)
        else:
            self.blocks_by_number[index] = [block]
        
        #determine if block shadows previous top block
        prev_hashes = block.block.prev_hashes
        for prev_hash in prev_hashes:
            if prev_hash in self.tops:
                del self.tops[prev_hash]

        #determine if block should be top block
        self.existing_links += prev_hashes
        if not block_hash in self.existing_links:
            self.tops[block_hash] = block

        self.add_txs_by_hash(block.block.system_txs)

        for listener in self.new_block_listeners:
            listener.on_new_block_added(block)
    
    def get_top_blocks(self):
        return self.tops
    
    def get_top_blocks_hashes(self):
        return list(self.get_top_blocks().keys())

    # just better name for get_top_blocks_hashes method
    def get_top_hashes(self):
        return self.get_top_blocks_hashes()

    def has_block_number(self, number):
        return number in self.blocks_by_number

    def get_block_number(self, block_hash):
        for number, block_list_by_number in self.blocks_by_number.items():
            for block_by_number in block_list_by_number:
                if block_by_number.block.get_hash() == block_hash:
                    return number
        assert False, "Cannot find block number for hash %r" % block_hash.hex()
        return -1
    
    def calculate_chain_length(self, top_block_hash):
        length = [0]
        top_block = self.blocks_by_hash[top_block_hash]
        self.recursive_previous_block_count(top_block, length)
        return length[0]

    def recursive_previous_block_count(self, block, count):
        count[0] += 1   # trick to emulate pass by reference
        for prev_hash in block.block.prev_hashes:
            block = self.blocks_by_hash[prev_hash]
            self.recursive_previous_block_count(block, count)

    def is_ancestor(self, block_hash, hash_to_find):
        if block_hash == hash_to_find:
            return True
            
        block = self.blocks_by_hash[block_hash]
        result = False
        for prev_hash in block.block.prev_hashes:
            if prev_hash == hash_to_find:
                return True
            result = result or self.is_ancestor(prev_hash, hash_to_find)
        return result

    # returns longest chain and chooses randomly if there are equal length longest chains
    def get_longest_chain_top_block(self, top_blocks):
        randgen = random.SystemRandom()  # crypto secure random
        randgen.shuffle(top_blocks)  # randomly shuffle tops so same length chains won't be chosen deterministically

        max_length = 0
        max_length_index = 0
        for i in range(0, len(top_blocks)):
            length = self.calculate_chain_length(top_blocks[i])
            if length > max_length:
                max_length = length
                max_length_index = i

        return top_blocks[max_length_index]

    def subscribe_to_new_block_notification(self, listener):
        self.new_block_listeners.append(listener)

    def collect_next_blocks(self, block_hash):
        next_blocks = []
        for block in self.blocks_by_hash:
            if block_hash in block.block.prev_hashes:
                next_blocks.append(block.get_hash())
        return next_blocks

    def get_branches_for_timeslot_range(self, start, end):
        all_blocks_in_range = {}
        for i in range(start,end):
            block_list = self.blocks_by_number.get(i,[])
            for block in block_list:
                all_blocks_in_range[block.block.get_hash()] = block.block

        links = []
        for block in all_blocks_in_range.values():
            links += block.prev_hashes
        
        for link in links:
            if link in all_blocks_in_range:
                del all_blocks_in_range[link]

        top_hashes = list(all_blocks_in_range.keys())

        return top_hashes

    def get_links(self, block_hash):
        assert block_hash in self.blocks_by_hash, "No block with such hash found"
        return self.blocks_by_hash[block_hash].block.prev_hashes

    def get_multiple_common_ancestor(self, chain_list):
        chains_blocks_lists = []
        iters = []
        length = len(chain_list)
        for i in range(length):
            chains_blocks_lists.append([])
            iterator = ChainIter(self, chain_list[i])
            iters.append(iterator)

        while True:  # TODO sane exit condition
            this_round_blocks = []
            for i in range(length):
                try:
                    block = iters[i].next()
                    if block:
                        block_hash = block.get_hash()
                        chains_blocks_lists.append(block_hash)
                        this_round_blocks.append(block_hash)
                except StopIteration:
                    pass

            for block in this_round_blocks:
                count = 0
                for block_list in chains_blocks_lists:
                    if block in block_list:
                        count += 1
                if count == length:
                    return block

        assert False, "No common ancestor found"
        return None

    # ------------------------------
    # transaction methods
    # ------------------------------
    def add_txs_by_hash(self, system_txs):
        for tx in system_txs:
            self.transactions_by_hash[tx.get_hash()] = tx
        return self.transactions_by_hash

    def get_tx_by_hash(self, tx_hash):
        result = self.transactions_by_hash.get(tx_hash)
        assert result, ("Cant find tx by hash", tx_hash)  # TODO remove ?
        return result

    def get_txs_by_type(self, tx_type):
        result = []
        for tx_hash, tx in self.transactions_by_hash:
            if isinstance(tx_type, NegativeGossipTransaction):
                if isinstance(tx, NegativeGossipTransaction):
                    result.append(tx)
            if isinstance(tx_type, PositiveGossipTransaction):
                if isinstance(tx, PositiveGossipTransaction):
                    result.append(tx)
            if isinstance(tx_type, PenaltyGossipTransaction):
                if isinstance(tx, PenaltyGossipTransaction):
                    result.append(tx)
        return result

    def get_negative_gossips(self):
        return self.get_txs_by_type(NegativeGossipTransaction())

    def get_positive_gossips(self):
        return self.get_txs_by_type(PositiveGossipTransaction())

    def get_penalty_gossips(self):
        return self.get_txs_by_type(PenaltyGossipTransaction())


# iterator over DAG, which uses first children only principle when traversing
# first argument is starting point
# returns None if block is skipped in the chain and block if it's present
# first call to next() is block with block_hash itself
# last one is genesis block
class ChainIter:
    def __init__(self, dag, block_hash):
        self.block_hash = block_hash
        self.dag = dag
        self.block_number = dag.get_block_number(block_hash)
        self.time_to_stop = False

    def __iter__(self):
        return self

    # in real implementation this method should return pair like (block number, block or None)
    def __next__(self):
        if self.time_to_stop:
            raise StopIteration()
        
        block_number = self.dag.get_block_number(self.block_hash)
        if block_number < self.block_number - 1:
            self.block_number -= 1
            return None
        
        if not self.block_hash in self.dag.blocks_by_hash:
            assert False, ("Can't find block in Dag", self.block_hash.hex())

        block = self.dag.blocks_by_hash[self.block_hash]
        self.block_number = block_number
        
        if block_number == 0:  # genesis block. Stop iteration on next()
            self.time_to_stop = True
        else:
            self.block_hash = block.block.prev_hashes[0]
        
        return block

    def next(self):
        return self.__next__()



