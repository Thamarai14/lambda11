import base64, random, string
from Cryptodome.Cipher import AES

BS = 16
pad = lambda s: s.decode('UTF-8') + (BS - len(s) % BS) * chr(BS - len(s) % BS) 
unpad = lambda s : s[:-ord(s[len(s)-1:])]

class AESCipher:
    def __init__( self, key ):
        self.key = key

    def encrypt( self, raw, iv ):
        
        raw = pad(raw)
        raw = bytes(raw, 'utf-8')
        cipher = AES.new( self.key, AES.MODE_CBC, iv )
        return base64.b64encode( cipher.encrypt( raw ) )

    def decrypt( self, enc, iv ):
        enc = base64.b64decode(enc)
        cipher = AES.new(self.key, AES.MODE_CBC, iv )
        return unpad(cipher.decrypt( enc )).decode('ascii', 'ignore')
    
    def ivkeygen(self):
        iv = ''.join(random.choices(string.ascii_letters, k=16))
        return iv
    
    
