from base64 import b64decode
from Crypto.PublicKey import RSA
from base64 import b64decode,b64encode

with open('keys') as f:
    lines = f.readlines()

for line in lines:
    decode = b64decode(line)
    if len(decode)!=0:
        key = RSA.importKey(decode)
        print(b64encode(key.publickey().exportKey('DER')).decode('utf-8'))
