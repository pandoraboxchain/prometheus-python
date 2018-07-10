class NodeApi():

    nodes = []
    def register_node(self, node):
        self.nodes.append(node)

    def get_list_of_actual_chains(self):
        return True

    def get_block_by_hash(self):
        return True

    def push_block(self, hash):
        return True

    def gossip_malicious(self, node_id):
        return True

    def broadcast_transaction(self, sender_node_id, raw_tx):
        for node in self.nodes:
            if node.node_id != sender_node_id:
                node.handle_transaction_message(sender_node_id, raw_tx)

    def broadcast_block(self, sender_node_id, raw_signed_block):
        for node in self.nodes:
            if node.node_id != sender_node_id:
                node.handle_block_message(sender_node_id, raw_signed_block)

    def broadcast_conflicting_block(self, sender_node_id, raw_signed_block):
        for node in self.nodes:
            if node.node_id != sender_node_id:
                node.handle_conflicting_block_message(sender_node_id, raw_signed_block)
