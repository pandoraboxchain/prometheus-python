class NodeApi:

    def __init__(self):
        self.nodes = []
        
    def register_node(self, node):
        self.nodes.append(node)

    @staticmethod
    def get_list_of_actual_chains():
        return True

    @staticmethod
    def get_block_by_hash():
        return True

    @staticmethod
    def push_block():
        return True

    @staticmethod
    def gossip_malicious():
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

    def broadcast_gossip_negative(self, sender_node_id, raw_gossip):
        for node in self.nodes:
            if node.node_id != sender_node_id:
                node.handle_gossip_negative(sender_node_id, raw_gossip)

    def broadcast_gossip_positive(self, sender_node_id, raw_gossip):
        for node in self.nodes:
            if node.node_id != sender_node_id:
                node.handle_gossip_positive(sender_node_id, raw_gossip)
