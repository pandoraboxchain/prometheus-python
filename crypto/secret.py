import random
import string

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from secretsharing import PlaintextToHexSecretSharer

def split_secret(key):
    s = "".join([random.choice(string.ascii_letters+string.digits) for i in range(20)])
    split_s = PlaintextToHexSecretSharer.split_secret(s, 51, 100)
    h = SHA256.new(s.encode("utf-8")).digest()
    IV = h[0:16]
    ekey = h[16:32]
    mode = AES.MODE_CBC
    encryptor = AES.new(ekey, mode, IV=IV)
    ciphertext = encryptor.encrypt(text)
    binPrivKey = key.exportKey('DER')
    p_text = b64encode(binPrivKey).decode('utf-8')
    while len(p_text) % 16 != 0:
        p_text+=' '
    ciphertext = encryptor.encrypt(p_text)
    return {
        "ciphertext": ciphertext,
        "splits": split_s,
    }

def decrypt_secret(splits, ciphertext):
    s = PlaintextToHexSecretSharer.recover_secret(splits)
    h = SHA256.new(s.encode("utf-8")).digest()
    IV = h[0:16]
    ekey = h[16:32]
    mode = AES.MODE_CBC
    decryptor = AES.new(ekey, mode, IV=IV)
    dpk = decryptor.decrypt(ciphertext)
    dpk = dpk.decode("utf-8").replace(' ','')
    key = RSA.importKey(b64decode(dpk))


def enc_part_secret(publickey, split):
    enc_data = publickey.encrypt(split.encode('utf-8'), 32)
    return enc_data

def dec_part_secret(privatekey, enc_data):
    split = privatekey.decrypt(enc_data)
    return split
