
class Keys:
    @staticmethod
    def from_bytes(key_bytes):
        return key_bytes

    @staticmethod
    def to_bytes(key):
        return key

    @staticmethod
    def list_from_bytes(key_bytes_list):
        decoded_keys = []
        for key in key_bytes_list:
            decoded_keys.append(Keys.from_bytes(key))
        return decoded_keys

    @staticmethod
    def list_to_bytes(keys_list):
        encoded_keys = []
        for key in keys_list:
            encoded_keys.append(Keys.to_bytes(key))
        return encoded_keys

    @staticmethod
    def to_visual_string(key):
        if not isinstance(key, (bytes, bytearray)):
            key = Keys.to_bytes(key)
        return key[0:13].hex()+"..."+key[-25:-12].hex()