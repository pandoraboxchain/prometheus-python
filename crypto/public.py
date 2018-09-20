#convenience class

class Public():
    @staticmethod
    def encrypt(message, key):
        return key.encrypt(message, 32)[0]
