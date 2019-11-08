import json
from base64 import b64encode, b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class AES256:

    def encrypt(self, data, key, iv):
        data = str.encode(data)
        key = str.encode(key)

        cipher = AES.new(key, AES.MODE_CBC, iv=str.encode(iv))
        # cipher = AES.new(key, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(data, AES.block_size))
        ct = b64encode(ct_bytes).decode('utf-8')
        return ct

    def decrypt(self, iv, cipher, key):
        try:
            iv = str.encode(iv)
            iv = b64encode(iv).decode('utf-8')
            iv = b64decode(iv)
            ct = b64decode(cipher)
            key = str.encode(key)
            cipher = AES.new(key, AES.MODE_CBC, iv)
            pt = unpad(cipher.decrypt(ct), AES.block_size)
            return pt

        except ValueError as ve:
            # return "Incorrect decryption value"
            return str(ve)
        except KeyError as ke:
            # return "Incorrect decryption key"
            return str(ke)
        finally:
            pass
