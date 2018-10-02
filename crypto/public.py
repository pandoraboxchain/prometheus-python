import seccure

class Public:
    @staticmethod
    def encrypt(message, key):
        return seccure.encrypt(message, key)

    @staticmethod
    def verify(message, signature, key):
        return seccure.verify(message, signature, key)
