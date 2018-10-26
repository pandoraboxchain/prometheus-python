import seccure
import os

class Private:

    #please note that following cache is shared across nodes and should not be implemented in production
    pubkey_cache = {}
    decrypt_cache = {}

    @staticmethod
    def generate():
        return os.urandom(32)
    
    @staticmethod
    def sign(message, key):
        return seccure.sign(message, key, seccure.SER_COMPACT, "secp256r1/nistp256")

    @staticmethod
    def encrypt(message, key):
        public_key = Private.publickey(key) #HACK
        return seccure.encrypt(message, public_key)

    @staticmethod
    def decrypt(message, key):
        args = (message, key)
        if not args in Private.decrypt_cache:
            try:
                result = seccure.decrypt(message, key, "secp256r1/nistp256")
            except: #decryption failure
                result = None
            Private.decrypt_cache[args] = result
        return Private.decrypt_cache[args]

    @staticmethod
    def publickey(private):
        if private not in Private.pubkey_cache:
            public = seccure.passphrase_to_pubkey(private, "secp256r1/nistp256").to_bytes(seccure.SER_COMPACT)
            Private.pubkey_cache[private] = public
        return Private.pubkey_cache[private]

