
class ConflictWatcher:
    def __init__(self, dag):
        self.dag = dag
        self.pubkeys_by_epochs = {}  # epoch number : public_key : block hashes list
        self.blocks = {}  # block hash : (public key, epoch_number)

    def on_new_block_by_validator(self, block_hash, epoch_number, public_key):
        self.blocks[block_hash] = (public_key, epoch_number)
        if not epoch_number in self.pubkeys_by_epochs:
            self.pubkeys_by_epochs[epoch_number] = {}
            
        if not public_key in self.pubkeys_by_epochs[epoch_number]:
            self.pubkeys_by_epochs[epoch_number][public_key] = [block_hash]            
        else:
            self.pubkeys_by_epochs[epoch_number][public_key].append(block_hash)

            # public_key : [block_hash]

    def get_conflicts_by_block(self, block_hash):
        assert block_hash in self.blocks, "No block in conflict watcher with hash %r" % block_hash.hex()
        pubkey, epoch_number = self.blocks[block_hash]
        return self.get_conflicts_by_pubkey(pubkey, epoch_number)

    def get_conflicts_by_pubkey(self, pubkey, epoch_number):
        conflicts = self.pubkeys_by_epochs[epoch_number][pubkey]
        if len(conflicts) == 1:
            return None
        return conflicts
        
    def find_conflicts_in_between(self, tops):
        common_ancestor = self.dag.get_common_ancestor(tops)
        common_ancestor_number = self.dag.get_block_number(common_ancestor)

        tops_numbers = [self.dag.get_block_number(top) for top in tops]
        latest_top_number = max(tops_numbers)

        merge_range = range(common_ancestor_number, latest_top_number + 1)

        all_merge_blocks = []
        for i in merge_range:
            for block in self.dag.blocks_by_number[i]:
                all_merge_blocks.append(block.get_hash())


        explicit_conflicts = [] # conflicts for sure, to be ignored
        candidate_conflicts = [] # one of these should be chosen by longest chain rule 

        for block in all_merge_blocks:
            conflicts = self.get_conflicts_by_block(block)
            if not conflicts:
                continue
            
            resolved_earlier = False
            inside_merge_conflicts = []
            for conflict in conflicts:
                conflict_number = self.dag.get_block_number(conflict)
                if conflict_number <= common_ancestor_number:
                    resolved_earlier = True
                    continue
                if conflict_number > latest_top_number:
                    continue
                
                inside_merge_conflicts.append(conflict)

            if resolved_earlier:
                explicit_conflicts += inside_merge_conflicts
            else:
                candidate_conflicts += [inside_merge_conflicts] #put candidates into conflict groups

            #delete blocks in conflict so we don't have same conflicts twice
            for block in inside_merge_conflicts:
                if block in all_merge_blocks:
                    all_merge_blocks.remove(block)
        
        return explicit_conflicts, candidate_conflicts

    def filter_out_longest_chain_conflicts(self, candidate_groups, longest_chain_top):
        explicit_conflicts = []
        for group in candidate_groups:
            sorted_group = sorted(group, key=lambda block: self.dag.get_block_number(block))
            for block in sorted_group:
                if self.dag.is_ancestor(longest_chain_top, block): #TODO maybe use chain iter search here?
                    sorted_group.remove(block)
                    break
            explicit_conflicts += sorted_group
        
        return explicit_conflicts
            