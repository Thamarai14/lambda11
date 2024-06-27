from sqlmodel import SQLModel, Field, MetaData,select, update, insert
from database.pgsqlconn import  db_session
import os
from dotenv import load_dotenv
from typing import Optional
from datetime import datetime
from utils.aes import AESCipher

load_dotenv()


meta = MetaData(schema= os.getenv("SCHEMA"))

ase_key = os.getenv('AES_SECRET_KEY')
aes_iv = os.getenv('AES_IV_KEY')

aes = AESCipher(ase_key.encode())

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


class tbl_tent_master(SQLModel, table = True):
    metadata = meta
    tent_id: Optional[int] = Field(default=None, primary_key=True)
    mast_tent_uuid : Optional[str] = Field(default=None,unique=True)
    tent_name: str
    tent_status: Optional[bool] = Field(default=True)
    
    
def find_tent_master_by_uuid(uuid : str):
    session = db_session()
    query = select(tbl_tent_master).where(tbl_tent_master.mast_tent_uuid == uuid)
    data = session.exec(query).first()
    session.close()
    return data

class tbl_tent_property_configuration(SQLModel, table = True):
    metadata = meta
    tent_property_config_id: Optional[int] = Field(default=None, primary_key=True, )
    tent_property_config_uuid:str
    tent_property_config_name:str
    tent_property_config_value:str
    category:str
    tent_id:int
    tent_property_config_status:bool
    created_by: int 
    property_type : str
    is_default:bool	


def old_update_insert(isupdate, normaldata:dict, tent_id):
    if isupdate:
        for key, value in normaldata.items():
            result = (update(tbl_tent_property_configuration).where(tbl_tent_property_configuration.tent_id==tent_id, tbl_tent_property_configuration.tent))

def is_default_update(tent_user_uuid, tent_id, category_name, category):
    session = db_session()
    try:
        print(category, category_name, "!!!!!!!!!!!!")
        result = (update(tbl_tent_integration).
                            where(tbl_tent_integration.integration_name!=category_name, tbl_tent_integration.integration_category==category, tbl_tent_integration.tent_id==tent_id).
                            values( is_default=False, modified_on=datetime.now(), modified_by=tent_user_uuid ))
        session.exec(result)
        session.commit()
    except Exception as exc:
        print(exc)
        session.rollback()
    finally:
        session.close()
    
    
    
def integration_update_insert(isUpdate, isDefault, tent_id, tent_user_id, category_name, category, enc_data, normal_data):
    session = db_session()
    try:
        if isUpdate:
            result = (update(tbl_tent_integration).
                    where(tbl_tent_integration.integration_name==category_name, tbl_tent_integration.tent_id==tent_id).
                    values(integration_value=enc_data, is_default=isDefault, modified_on=datetime.now(), modified_by=tent_user_id ))
            if isDefault:
                is_default_update(tent_user_id, tent_id, category_name, category)
            session.exec(result)
            session.commit()
            
        else:
            s_query=select(tbl_tent_integration).where(tbl_tent_integration.integration_name==category_name, tbl_tent_integration.tent_id==tent_id)
            data = session.exec(s_query).first()
            session.close()
            session = db_session()
            if not data:
                result = (insert(tbl_tent_integration).
                        values(integration_category=category, integration_name=category_name, integration_value=enc_data, is_default=isDefault, created_by=tent_user_id, tent_id=tent_id, tent_user_id=tent_user_id))
                if isDefault:
                    is_default_update(tent_user_id, tent_id, category_name, category)
                session.exec(result)
                session.commit()
            else:
                return False
            
            
    except Exception as exc:
        print(exc)
        session.rollback()
        return False
    finally:
        session.close()       
        
        
        
def get_integration(tent_id, category_name):
    session = db_session()
    try:
        query = select(tbl_tent_integration).where(tbl_tent_integration.tent_id==tent_id, tbl_tent_integration.integration_name==category_name)
        result = session.exec(query).first()
        session.close()
        return result
        
        
    except:
        session.rollback()
        session.close()
        return None
    finally:
        session.close()


def tent_property_configuration_insertion(insertion_values:dict, tent_id:int, category_name:str, tent_integration_name:str, isDefault:bool):
    session = db_session()
    delete_query = f"delete from aidivaa.tbl_tent_property_configuration where tent_id = {tent_id} and category = '{category_name}'"
    session.exec(delete_query)
    session.commit()
    session.close()
    session = db_session()
    for key in insertion_values:
        property_value = insertion_values[key]
        enc_value = aes.encrypt(property_value.encode(), aes_iv.encode())
        encrypted_text = enc_value.decode()
        result = (insert(tbl_tent_property_configuration).values(tent_property_config_name = key,tent_property_config_value = encrypted_text ,category=category_name, property_type=tent_integration_name,  is_default=isDefault, created_by=tent_id, tent_id=tent_id))
        try:
            session.exec(result)
            session.commit()
        except Exception as exec:
            session.rollback()
            return None
        finally:
            session.close()
    return True


def get_tenant_integeration_config(tent_id:int, integration_category:str, integration_name:str)->dict:
    session = db_session()
    query = select(tbl_tent_integration).where(tbl_tent_integration.tent_id == tent_id).where(tbl_tent_integration.integration_category == integration_category).where(tbl_tent_integration.integration_name == integration_name)
    properies_data = session.exec(query).first()
    session.close()
    decrypted_text = ''
    if properies_data != None:
        decrypted_text = aes.decrypt(properies_data.integration_value, aes_iv.encode("utf8"))
        return decrypted_text
    return None


def get_old_propery_integeration(tent_id:int, integration_category:str, tent_property_config_name:str)->dict:
    try:
        session = db_session()
        query = select(tbl_tent_property_configuration).where(tbl_tent_property_configuration.tent_id == tent_id).where(tbl_tent_property_configuration.tent_property_config_name == tent_property_config_name).where(tbl_tent_property_configuration.category == integration_category)
        properies_data = session.exec(query).first()
        decrypted_text = ''
        if properies_data != None:
            # decrypted_text = aes.decrypt(properies_data.tent_property_config_value, aes_iv.encode("utf8"))
            decrypted_text = aes.decrypt(properies_data.tent_property_config_value, aes_iv.encode("utf8"))
            return decrypted_text
        return None
    except:
        session.rollback()
    finally:
        session.close()
        