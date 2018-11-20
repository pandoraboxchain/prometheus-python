
class SkippedBlock:
    def __init__(self, anchor_block_hash, backstep_count):
        self.anchor_block_hash = anchor_block_hash
        self.backstep_count = backstep_count

    @staticmethod
    def is_skipped(block):
        if not block:
            return True
        if isinstance(block, SkippedBlock):
            return True
        
        return False


