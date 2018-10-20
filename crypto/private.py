import seccure
import os

class Private:

    cache = {}

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
        return seccure.decrypt(message, key, "secp256r1/nistp256")

    @staticmethod
    def publickey(private):
        if private not in Private.cache:
            public = seccure.passphrase_to_pubkey(private, "secp256r1/nistp256").to_bytes(seccure.SER_COMPACT)
            Private.cache[private] = public
        return Private.cache[private]

