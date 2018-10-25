class Network:

    def __init__(self, *groups):
        self.nodes = []
        self.groups = None
        self.merge_groups_flag = False
        if groups:
            self.groups = {}
            for group in groups:
                self.groups[group] = []

    def register_node(self, node, *group_ids):
        if group_ids:
            for group_id in group_ids:
                group = self.groups[group_id]
                group.append(node)
        else:
            self.nodes.append(node)

    def move_nodes_to_group(self, group_id, nodes_list):
        if not self.groups: self.groups = {}
        if group_id not in self.groups:
            self.groups[group_id] = []
        for node in nodes_list:
            group = self.groups[group_id]
            group.append(node)
            if node in self.nodes:
                self.nodes.remove(node)

    @staticmethod
    def get_list_of_actual_chains():
        return True

    @staticmethod
    def push_block():
        return True

    # request receiver_node_id (node) by getting SignedBlock() by HASH.
    # receiver MUST response by SignedBlock() else ?(+1 request to ANOTHER node - ?)
    def get_block_by_hash(self, sender_node_id, receiver_node_id, block_hash):
        if self.groups:
            if self.merge_groups_flag:
                self.merge_all_groups()
            else:
                self.nodes = self.get_nodes_group_by_sender_node_id(sender_node_id)
        if self.check_node_output_transport_behaviour(sender_node_id):
            return
        for node in self.nodes:
            if self.check_node_input_transport_behaviour(receiver_node_id):
                return
            if node.node_id == receiver_node_id:
                node.request_block_by_hash(block_hash=block_hash)

    def broadcast_transaction(self, sender_node_id, raw_tx):
        if self.groups:
            if self.merge_groups_flag:
                self.merge_all_groups()
            else:
                self.nodes = self.get_nodes_group_by_sender_node_id(sender_node_id)
        if self.check_node_output_transport_behaviour(sender_node_id):
            return
        for node in self.nodes:
            if self.check_node_input_transport_behaviour(node.node_id):
                return
            if node.node_id != sender_node_id:
                node.handle_transaction_message(sender_node_id, raw_tx)

    def broadcast_block(self, sender_node_id, raw_signed_block):
        if self.groups:
            if self.merge_groups_flag:
                self.merge_all_groups()
            else:
                self.nodes = self.get_nodes_group_by_sender_node_id(sender_node_id)
        if self.check_node_output_transport_behaviour(sender_node_id):
            return
        for node in self.nodes:
            if self.check_node_input_transport_behaviour(node.node_id):
                return
            if node.node_id != sender_node_id:
                node.handle_block_message(sender_node_id, raw_signed_block)

    def broadcast_block_out_of_timeslot(self, sender_node_id, raw_signed_block):
        if self.groups:
            if self.merge_groups_flag:
                self.merge_all_groups()
            else:
                self.nodes = self.get_nodes_group_by_sender_node_id(sender_node_id)
        if self.check_node_output_transport_behaviour(sender_node_id):
            return
        for node in self.nodes:
            if self.check_node_input_transport_behaviour(node.node_id):
                return
            if node.node_id != sender_node_id:
                node.handle_block_out_of_timeslot(sender_node_id, raw_signed_block)

    def broadcast_gossip_negative(self, sender_node_id, raw_gossip):
        if self.groups:
            if self.merge_groups_flag:
                self.merge_all_groups()
            else:
                self.nodes = self.get_nodes_group_by_sender_node_id(sender_node_id)
        if self.check_node_output_transport_behaviour(sender_node_id):
            return
        for node in self.nodes:
            if self.check_node_input_transport_behaviour(node.node_id):
                return
            if node.node_id != sender_node_id:
                node.handle_gossip_negative(sender_node_id, raw_gossip)

    def broadcast_gossip_positive(self, sender_node_id, raw_gossip):
        if self.groups:
            if self.merge_groups_flag:
                self.merge_all_groups()
            else:
                self.nodes = self.get_nodes_group_by_sender_node_id(sender_node_id)
        if self.check_node_output_transport_behaviour(sender_node_id):
            return
        for node in self.nodes:
            if self.check_node_input_transport_behaviour(node.node_id):
                return
            if node.node_id != sender_node_id:
                node.handle_gossip_positive(sender_node_id, raw_gossip)

    # request block by has directly from node without broadcast
    def direct_request_block_by_hash(self, sender_node_id, receiver_node_id, block_hash):
        if self.groups:
            if self.merge_groups_flag:
                self.merge_all_groups()
            else:
                self.nodes = self.get_nodes_group_by_sender_node_id(sender_node_id)
        if self.check_node_output_transport_behaviour(sender_node_id):
            return
        for node in self.nodes:
            if self.check_node_input_transport_behaviour(receiver_node_id):
                return
            if node.node_id == receiver_node_id:
                node.direct_request_block_by_hash(sender_node_id, receiver_node_id, block_hash)

    def direct_response_block_by_hash(self, sender_node_id, receiver_node_id, raw_signed_block):
        if self.groups:
            if self.merge_groups_flag:
                self.merge_all_groups()
            else:
                self.nodes = self.get_nodes_group_by_sender_node_id(sender_node_id)
        if self.check_node_output_transport_behaviour(sender_node_id):
            return
        for node in self.nodes:
            if self.check_node_input_transport_behaviour(receiver_node_id):
                return
            if node.node_id == receiver_node_id:
                node.handle_block_out_of_timeslot(sender_node_id, raw_signed_block)

    # -----------------------------------------------------------------
    # internal methods
    # -----------------------------------------------------------------
    def merge_all_groups(self):
        for group in self.groups:
            node_group = self.groups[group]
            for node in node_group:
                if node not in self.nodes:
                    self.nodes.append(node)
        self.groups = None
        self.merge_groups_flag = False

    def get_nodes_group_by_sender_node_id(self, sender_node_id):
        for group in self.groups:
            nodes_in_group = self.groups[group]
            for node in nodes_in_group:
                if sender_node_id == node.node_id:
                    return nodes_in_group

    def check_node_input_transport_behaviour(self, receiver_node_id):
        # get node by id and validate behaviour for receive requests
        for node in self.nodes:
            if node.node_id == receiver_node_id:
                if node.behaviour.transport_node_disable_input:
                    return True
        return False

    def check_node_output_transport_behaviour(self, sender_node_id):
        # get node by id and validate behaviour for broadcast data
        for node in self.nodes:
            if node.node_id == sender_node_id:
                if node.behaviour.transport_node_disable_output:
                    return True
        return False


