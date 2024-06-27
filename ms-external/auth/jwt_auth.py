import jwt
import time
from dotenv import load_dotenv
import os
import pytz
from utils.aes import AESCipher
import json
load_dotenv()

aes_secret_key = os.getenv("AES_SECRET_KEY")
aes_iv_key = os.getenv("AES_IV_KEY")

jwt_secret_key = os.getenv("JWT_SECRET")
jwt_algorithm = os.getenv("JWT_ALGORITHM")
IST = pytz.timezone('Asia/Kolkata')


aesObj = AESCipher(aes_secret_key.encode())

def generate_token(token:str):
    return {"access_token":token}

def encode_token(email:str, lyfngo_account_id:str,developer_id:str):
    payload = {
        "email":email,
        "lyfngoAccountId":lyfngo_account_id,
        "developerId":developer_id,
        "expiry_time": time.time()+31536000
    }
    # encrypted_text = aesObj.encrypt(json.dumps(payload).encode(),aes_iv_key.encode())
    # encode_token = jwt.encode({"data":str(encrypted_text)},jwt_secret_key, algorithm= jwt_algorithm)
    encode_token = jwt.encode(payload,jwt_secret_key, algorithm= jwt_algorithm)
    return generate_token(encode_token)

def decode_token(token:str):
    # decode_token = jwt.decode(token, jwt_secret_key, jwt_algorithm)
    # decrypted_dict = json.loads(aesObj.decrypt(decode_token['data'].encode(),aes_iv_key.encode()))
    decode_token = jwt.decode(token, jwt_secret_key, jwt_algorithm)
    if decode_token['expiry_time'] > time.time():
        return True
    else:
        return False
