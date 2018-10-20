import seccure

class Public:
    cache = {}
    @staticmethod
    def encrypt(message, key):
        return seccure.encrypt(message, key)

    @staticmethod
    def verify(message, signature, key):
        args = (message, signature, key)
        if not args in Public.cache:
            result = seccure.verify(message, signature, key)
            Public.cache[args] = result
        return Public.cache[args]
