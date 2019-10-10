import json
from base64 import b64encode, b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class AES256:

    def encrypt(self, data, key, iv):
        data = str.encode(data)
        key = str.encode(key)

        cipher = AES.new(key, AES.MODE_CBC, iv=str.encode(iv))
        ct_bytes = cipher.encrypt(pad(data, AES.block_size))
        ct = b64encode(ct_bytes).decode('utf-8')
        print(ct)

    def decrypt(self, iv, cipher, key):
        try:
            iv = b64decode(iv)
            ct = b64decode(cipher)
            key = str.encode(key)
            cipher = AES.new(key, AES.MODE_CBC, iv)
            pt = unpad(cipher.decrypt(ct), AES.block_size)
            print(pt)
        except ValueError as ve:
            print("Incorrect decryption value")
        except KeyError as ke:
            print("Incorrect decryption key")
        finally:
            pass
