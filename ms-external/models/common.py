from fastapi import APIRouter, Request, HTTPException 
from sqlmodel import SQLModel, Field, MetaData,select
from database.pgsqlconn import engine
from typing import Optional, List
import enum, os ,bcrypt
from dotenv import load_dotenv
from utils.aes import AESCipher
from database.pgsqlconn import db_session
from datetime import datetime, timezone ,timedelta
import pytz
import jwt
import random
from auth.jwt_auth import encode_token, decode_token
from utils.apicalllog import request_session
import json,re

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
requests = request_session()
load_dotenv()
requests = request_session()
meta = MetaData(schema= os.getenv("SCHEMA"))
db_schema = os.getenv("SCHEMA")
deckey = os.getenv("AES_SECRET_KEY")
iv = os.getenv("AES_IV_KEY")
aes_obj = AESCipher(deckey.encode("utf8"))
IST = pytz.timezone('Asia/Kolkata')

mongo_db_url = os.getenv("MONGO_DB_URL")
wa_lyfngo_phone_id = os.getenv("WA_LYFNGO_PHONE_ID")
wa_lyfngo_token = os.getenv("WA_LYFNGO_TOKEN")
wa_lyfngo_busienss_account_id = os.getenv("WA_LYFNGO_BUSSINESS_ACCOUNT_ID")
wa_lyfngo_version = os.getenv("WA_VERSION")
try:
    cluster = MongoClient(mongo_db_url)
except ConnectionFailure:
    raise HTTPException(status_code=403, detail="err_mongo_connection")

db_name = cluster["whatsappbot"]
zoho_crm_history_coll = db_name["zoho_crm_history"]

class tbl_tent_master(SQLModel, table = True):
    metadata = meta
    tent_id: Optional[int] = Field(default=None, primary_key=True)
    mast_tent_uuid : Optional[str] = Field(default=None,unique=True)
    # developer_id : Optional[str] = Field(default=None,unique=True)
    tent_name: str
    tent_status: Optional[bool] = Field(default=True)
    
class tbl_lyfngo_developer_account(SQLModel, table = True):
    metadata = meta
    developer_account_id: Optional[int] = Field(default=None, primary_key=True)
    developer_account_uuid : Optional[str] = Field(default=None,unique=True)
    lyfngo_developer_account_status: Optional[bool] = Field(default=True)
    lyfngo_permanent_token : Optional[str]
    lyfngo_token_created_on : Optional[datetime] = Field(default=datetime.now(IST))
    lyfngo_token_expired_on : Optional[datetime] = Field(default=datetime.now(IST) + timedelta(days=365))
    tent_id: int = Field(foreign_key="tbl_tent_master.tent_id")
    created_by: int
    modified_by: Optional[int]
    developer_id : Optional[str] = Field(default=None,unique=True)

    
    
def find_developer_account_by_tent_id(tent_id : int):
    try:
        session = db_session()
        query = select(tbl_lyfngo_developer_account).where(tbl_lyfngo_developer_account.tent_id == tent_id)
        data = session.exec(query).first()
        return data
    except:
        session.rollback()
    finally:
        session.close()

def find_tent_master_by_uuid(uuid : str):
    try:
        session = db_session()   
        query = select(tbl_tent_master).where(tbl_tent_master.mast_tent_uuid == uuid)
        data = session.exec(query).first()
        return data
    except:
        session.rollback()
    finally:
        session.close()

def find_tent_master_by_developer_id(developer_id : str):
    try:
        session = db_session()   
        query = select(tbl_lyfngo_developer_account,tbl_tent_master).join(tbl_tent_master).where(tbl_lyfngo_developer_account.developer_id == developer_id)
        data = session.exec(query).first()
        return data
    except:
        session.rollback()
    finally:
        session.close()

def find_lyfngo_developer_account_by_developer_id(developer_id : str):
    try:
        session = db_session()   
        query = select(tbl_lyfngo_developer_account).where(tbl_lyfngo_developer_account.developer_id == developer_id)
        data = session.exec(query).first()
        return data
    except:
        session.rollback()
    finally:
        session.close()


def check_password(tent_uuid:str , password:str ,email:str):
    try:
        session = db_session()   
        query = f''' select ttui.tent_user_identity_password from {db_schema}.tbl_tent_user ttu
            inner join {db_schema}.tbl_tent_user_role_mapping tturm on tturm.tent_user_id = ttu.tent_user_id
            inner join {db_schema}.tbl_tent_master ttm on ttm.tent_id = ttu.tent_id
            inner join {db_schema}.tbl_tent_user_identity ttui on ttui.tent_user_identity_id = ttu.tent_user_identity_id
            where tturm.mast_role_id = 1 and ttm.mast_tent_uuid ='{tent_uuid}' and ttui.tent_user_identity_email= '{email}' '''
        result = session.exec(query).first()
        if result:
            pwd_hash = result.tent_user_identity_password
            pwd_hash =pwd_hash.encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), pwd_hash):
                return True
        return False
    except:
        session.rollback()
    finally:
        session.close()

def developer_account_creation(json_input:dict):
    try:
        session = db_session()
        uuid_query = f"select {db_schema}.gen_uuid()"
        uuid = session.exec(uuid_query).first()
        add_data = tbl_lyfngo_developer_account(tent_id=json_input['tent_id'],developer_account_uuid = uuid['gen_uuid'],created_by=json_input['tent_id'],modified_by = json_input['tent_id'],lyfngo_developer_account_status = True, developer_id = str(random.randint(10**15, 10**16 - 1)))
        session.add(add_data)
        session.commit()
        session.refresh(add_data)
        if add_data.developer_account_id != None:
            token = encode_token(json_input['email'],lyfngo_account_id = json_input['tent_id'],developer_id = add_data.developer_id)
            query=select(tbl_lyfngo_developer_account).where(tbl_lyfngo_developer_account.developer_account_id==add_data.developer_account_id)
            tbl_lyfngo_dict =session.exec(query).first()
            setattr(tbl_lyfngo_dict, "lyfngo_permanent_token", token['access_token'])
            session.add(tbl_lyfngo_dict)
            session.commit()
            session.refresh(tbl_lyfngo_dict)
            return tbl_lyfngo_dict
        return None
    except:
        session.rollback()
    finally:
        session.close()

def validate_token_developer_id(developer_id:str, token:str):
    jwt_secret_key = os.getenv("JWT_SECRET")
    jwt_algorithm = os.getenv("JWT_ALGORITHM")
    decode_token = jwt.decode(token, jwt_secret_key, jwt_algorithm)

    if decode_token['developerId'] == developer_id :
        return find_lyfngo_developer_account_by_developer_id(developer_id)
    return None

def validate_api(tent_id:str, api:str):
    try:
        session = db_session()
        query = f"select allowed_api from aidivaa.tbl_lyfngo_developer_account where tent_id = {tent_id} "
        data = session.exec(query).first()
        if data.allowed_api == None:
            return False
        if api in list(data.allowed_api):
            return True
        return False
    except:
        session.rollback()
    finally:
        session.close()

def get_customer_list_by_tent_id(tent_id,mobile_number:str):
    try:
        session = db_session()
        customer_query  = f" and tcm.cust_mobile_no = '{mobile_number}'" if mobile_number != None else ' '
        query = (f'''select tcm.cust_name,concat(tcm.cust_country_code,tcm.cust_mobile_no) as mobile_number ,tcm.cust_email,tcm.cust_uuid as cust_id 
                from {db_schema}.tbl_cust_master tcm 
                inner join {db_schema}.tbl_tent_master ttm on ttm.tent_id = tcm.tent_id 
                where tcm.cust_status is true and tcm.is_hard_delete is false and tcm.cust_name is not null and tcm.tent_id = {tent_id}  {customer_query} order by tcm.cust_name asc ''')    
        result = session.exec(query).all()
        return result
    except:
        session.rollback()
    finally:
        session.close()

class tbl_tent_integration(SQLModel, table=True):
    metadata = meta
    integration_id:Optional[int] = Field(default=None, primary_key=True)	
    integration_uuid:str	
    integration_name:str	
    integration_value:str	
    integration_category:str	
    is_default:bool	
    created_on:datetime	
    created_by:	int
    modified_on	:datetime
    modified_by	:int
    tent_id	:int
    tent_user_id:int

def get_tenant_integeration_config(tent_id:int, integration_category:str, integration_name:str)->dict:
    try:
        session = db_session()
        query = select(tbl_tent_integration).where(tbl_tent_integration.tent_id == tent_id).where(tbl_tent_integration.integration_category == integration_category).where(tbl_tent_integration.integration_name == integration_name)
        properies_data = session.exec(query).first()
        decrypted_text = ''
        if properies_data != None:
            decrypted_text = aes_obj.decrypt(properies_data.integration_value, iv.encode("utf8"))
            return decrypted_text
        return None
    except:
        session.rollback()
    finally:
        session.close()



def send_wa_message(phone_number_id:str, wa_version:str, token:str, to:str, message:str)->dict:
    url = f"https://graph.facebook.com/v{wa_version}/{phone_number_id}/messages"
    payload = json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": f"{to}",
        "type": "text",
        "text": {
            "preview_url": False,
            "body": f"{message}"
        }
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


class tbl_cust_master(SQLModel, table = True):
    metadata = meta
    cust_id: Optional[int] = Field(default=None, primary_key=True)
    cust_uuid : Optional[str] = Field(default=None,unique=True)
    cust_name: str
    cust_mobile_no: str
    cust_email: str
    cust_country_code: str
    tent_id:Optional[int]
    cust_identity_id:Optional[int]
    cust_status: Optional[bool] = Field(default=True)
    woocommerce_id:Optional[int]
  
def wooc_id_update_to_customer(cust_uuid:str,woocommerce_id:int):
    try:
        session = db_session()
        query=select(tbl_cust_master).where(tbl_cust_master.cust_uuid==cust_uuid)
        tbl_cust_master_dict =session.exec(query).first()
        setattr(tbl_cust_master_dict, "woocommerce_id", woocommerce_id)
        session.add(tbl_cust_master_dict)
        session.commit()
        session.refresh(tbl_cust_master_dict)
        return tbl_cust_master_dict
    except:
        session.rollback()
    finally:
        session.close()


def get_customer_by_attrs(tent_id,mobile_number,email):
    try:
        session  = db_session()
        query = f" select cust_id,cust_uuid from aidivaa.tbl_cust_master tcm where tent_id = {tent_id} and (cust_mobile_no = '{mobile_number}' or cust_email  = '{email}') "
        data = session.exec(query).first()
        return data
    except:
        session.rollback()
    finally:
        session.close()

def get_customer_by_wooc_id(wooc_id):
    try:
        session  = db_session()
        query = f" select cust_id,cust_uuid from aidivaa.tbl_cust_master tcm where woocommerce_id =  {wooc_id}"
        data = session.exec(query).first()
        return data
    except:
        session.rollback()
    finally:
        session.close()
    
def get_product_by_wooc_id(wooc_id):
    try:
        session  = db_session()
        query = f" select tent_product_id,tent_product_uuid from aidivaa.tbl_tent_product_master tpm where woo_commerce_id =  {wooc_id}"
        data = session.exec(query).first()
        return data
    except:
        session.rollback()
    finally:
        session.close()


def update_user_status(mast_tent_group_uuid:str,tent_user_identity_uuid:str,tent_user_uuid:str):
    try:
        session  = db_session()
        query = f"select tent_group_id {db_schema}.tbl_tent_group ttg where group_uuid = '{mast_tent_group_uuid}' "
        result = session.exec(query).first()

        query = f"""update {db_schema}.tbl_tent_user_identity  SET is_email = true,is_mobile= true WHERE tent_user_identity_uuid ='{tent_user_identity_uuid}' """
        session.exec(query)
        session.commit()
        # checkout timings
        query = f"""
            update {db_schema}.tbl_tent_user  SET is_email = true,is_mobile= true,is_welcome=true,mast_tent_group_id={result['mast_tent_group_id']} WHERE tent_user_uuid ='{tent_user_uuid}'
        """
        session.exec(query)
        session.commit()
    except:
        session.rollback()
        # session.close()
    finally:
        session.close()

# def get_laguage_by_tent_id(mast_tent_uuid:str):
#     try:
#         session  = db_session()
#         query = f""" select tml.mast_lookup_value as language_name ,tml.mast_lookup_key as lang_code from (SELECT unnest(string_to_array(cast(tent_comm_language as varchar), ',')) AS lang_code 
#     from aidivaa.tbl_tent_master where mast_tent_uuid = '{mast_tent_uuid}') as lan inner join aidivaa.tbl_mast_lookup tml on tml.mast_lookup_key = lan.lang_code
#     where  mast_lookup_type = 'PLA' """
#         data = session.exec(query).all()
#         return data
#     except:
#         session.rollback()
#     finally:
#         session.close()  
# 
async def zoho_crm_history(insert_data:dict):
    timezone = pytz.timezone('Asia/Kolkata')
    insert_data['created_on']=datetime.now(timezone)
    zoho_crm_history_coll.insert_one(insert_data) 
    return True



async def wa_template_messages_get(bussiness_id:str,variables:dict, token:str, template_name:str, wa_version:str='v17.0'):
    """
    owner : Linga <lingaprasath.m@rigelsoft.com>
    desc : function to find tempaltes messages dynamically
    return : mixed
    input type :string, dict
    """
    replace_find_pattern = r'{{(.*?)}}'
    url = f"https://graph.facebook.com/{wa_version}/{bussiness_id}/message_templates?name={template_name}"

    payload = ""
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    response_json=response.json()
    message_body=''
    if response_json.get('data') and response.status_code == 200:
        components = response_json['data'][0]['components']
        for template_type in components:
            if template_type.get('type') == 'BODY' and template_type.get('text'):
                message_body += template_type.get('text') 
            if template_type.get('type') == 'FOOTER' and template_type.get('text'):
                message_body +='\n\n'+template_type.get('text')

        def __replace_match(match):
            return variables.get(match.group(1), match.group(0))
        print_text = re.sub(replace_find_pattern, __replace_match, message_body)
        return print_text
    return None




async def wa_opt_out_check(phone_number_id:str,customer_mobile_number:str):
    """
    Author : Linga <lingaprasath.m@rigelsoft.com>
    desc : function to check opt out feature
    return : mixed
    input type :string, dict
    """
    opt_out_collection=db_name['whatsapp_optout']
    opt_out_exist = opt_out_collection.find_one({
        "number":customer_mobile_number,
        "phone_number_id":phone_number_id
    })
    if opt_out_exist:
        return None
    return True


# The `TemplatePatten` class is a Python class that represents a template pattern for sending messages
# using the WhatsApp API.
class TemplatePatten:
    
    
    def __init__(self,  **kwargs):    
        """
        ``TemplatePatter``
        ``a = TemplatePatter(template_name="template_name", mobile_number="number", country_code="conutrycode",template_params={1:name, 2:date} )``
        if bool(a) is true means template fetched and formeted next call send message function
        if bool(a) is false
        then run ``str(a)`` to get the error str
        """
        """
        The above code defines a class that handles the parsing and sending of WhatsApp messages using
        Facebook's Graph API.
        """
        self.template_name = kwargs.get("template_name")
        self.template_json = None
        self.template_params = kwargs.get("template_params", {})
        self.other_kwargs = kwargs
        self.actual_body_params = None
        self.pattern = r'\{\{(.+?)\}\}'
        self.meta_header  = {
            'Authorization': f'Bearer {wa_lyfngo_token}'
        }
        self.meta_language = None
        self.actual_message_body = None
        self.get_template_from_meta()
        self.template_parse()
    
    def __bool__(self):
        """
        The function checks if the length of two lists is equal and returns True if they are, otherwise
        it returns False.
        :return: The code is returning a boolean value. If the `self.actual_body_params` is a list and
        its length is equal to the length of `self.template_params`, then it returns `True`. Otherwise,
        it returns `False`.
        """
        if isinstance(self.actual_body_params, list):
            if len(self.actual_body_params) == len(self.template_params):
                return True
        return False
        
    def __repr__(self) -> str:
        if isinstance(self.actual_body_params, list):  
            if len(self.actual_body_params) != len(self.template_params):
                return f"Given params is {len(self.template_params)} but meta needs {len(self.actual_body_params)}"
        return "Unable to fetch the template"
        
    def template_parse(self):
        if self.template_json:
            components = self.template_json['data'][0]['components']
            self.meta_language = self.template_json['data'][0]["language"]
            message_body = ''
            for body_data in components:
                if body_data["type"]=="BODY":
                    actual_template = body_data["text"]
                    matches = re.findall(self.pattern, actual_template)
                    self.actual_body_params = matches
                    message_body +='\n\n'+body_data.get('text')
                if body_data.get('type') == 'FOOTER' and body_data.get('text'):
                    message_body +='\n\n'+body_data.get('text')
            def __replace_match(match):
                return self.template_params.get(match.group(1), match.group(0))
            self.actual_message_body = re.sub(self.pattern, __replace_match, message_body)
        
  
    def get_template_from_meta(self):
        url = f"https://graph.facebook.com/{wa_lyfngo_version}/{wa_lyfngo_busienss_account_id}/message_templates?template_name={self.template_name}"

        
        
        response = requests.request("GET", url, headers=self.meta_header)
        response_json=response.json()
        if response_json.get('data') and response.status_code == 200:
            self.template_json=response_json
      
    def send_message(self)-> dict:
        """``return {"response":"request type", "request":"dict"}``"""
        mobile_number = self.other_kwargs.get("mobile_number")
        country_code = self.other_kwargs.get("country_code")
        ordered_dict = dict(sorted(self.other_kwargs.get("template_params").items()))
        final_var = []
        for _, value in ordered_dict.items():
            final_var.append({
                "type": "text",
                "text":value
            })
    
        message_json= {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": f"{country_code}{mobile_number}",
            "type": "template",
            "template": {
                "name": self.other_kwargs.get("template_name"),
                "language": {
                "code": self.meta_language
                },
                "components": [
                {
                    "type": "body",
                    "parameters": final_var
                }
                ]
            }
            }
        
        url = f"https://graph.facebook.com/{wa_lyfngo_version}/{wa_lyfngo_phone_id}/messages"
        wa_response = requests.request(
            "POST", url, headers=self.meta_header, json=message_json)
        return {"response":wa_response, "requests":message_json}   
    
    
    
    
