class NodeApi():

    nodes = []
    def __init__(self, node):
        self.nodes.append(node)

    def get_list_of_actual_chains(self):
        return True

    def get_block_by_hash(self):
        return True

    def push_block(self, hash):
        return True

    def gossip_malicious(self, node_id):
        return True

    def broadcast_block(self, raw_signed_block):
        return True
