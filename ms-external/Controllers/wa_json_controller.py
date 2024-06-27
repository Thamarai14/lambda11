# from fastapi import APIRouter, HTTPException, Request
# # from fastapi.encoders import jsonable_encoder
# # from fastapi.responses import JSONResponse
# from pymongo import MongoClient
# from pymongo.errors import ConnectionFailure
# # from bson.objectid import ObjectId
# # from bson.json_util import dumps
# import os
# from dotenv import load_dotenv
# import re
# # import json
# wa_json = APIRouter()
# from models.wa_api import send_wa_message
# from utils.wa_api_methods import get_group_list,get_tent_type_list,get_speciality_list,get_lyfngo_countries_list,get_lyfngo_states_list,tent_registration,get_language_list,load_customised_templates,flows_list,send_custom_interactive


# import datetime as dt
# import pytz

# from datetime import datetime

# load_dotenv()
# mongo_db_url = os.getenv("MONGO_DB_URL")
# # Connecting to the database and creating a collection.
# try:
#     cluster = MongoClient(mongo_db_url)
# except ConnectionFailure:
#     raise HTTPException(status_code=404, detail="err_mongo_connection")
# db_name = cluster["json_bot"]
# wa_json_coll = db_name["wa_json"]
# current_block_coll = db_name["cust_current_block"]
# wa_chat_history_coll = db_name['wa_chat_history']


# timezone = pytz.timezone('Asia/Kolkata')
# current_date = datetime.now(timezone)

# def tent_wa_json(mast_tent_uuid:str):
#     result_data_dict = wa_json_coll.find_one({"tent_id": mast_tent_uuid})
#     if result_data_dict == None:
#         return None
#     del result_data_dict['_id'] 
#     return result_data_dict

# def tent_wa_json_block(mast_tent_uuid:str):
#     result_data_dict = wa_json_coll.find_one({"tent_id": mast_tent_uuid})
#     if result_data_dict == None:
#         return None
#     del result_data_dict['_id'] 
#     return result_data_dict['blocks']

# def fn_upcoming_block(mobile_number:str,mast_tent_uuid:str):
#     cust_var = fn_cust_current_block_json(mobile_number=mobile_number,mast_tent_uuid=mast_tent_uuid)
#     cust_index_number = cust_var['current_block']
#     result_data_dict = wa_json_coll.find_one({"tent_id": mast_tent_uuid})
#     if result_data_dict == None:
#         return None
#     del result_data_dict['_id'] 
#     return result_data_dict['blocks'][cust_index_number]

# def fn_cust_index_number(mobile_number:str,mast_tent_uuid:str):
#     cust_var = fn_cust_current_block_json(mobile_number=mobile_number,mast_tent_uuid=mast_tent_uuid)
#     cust_index_number = cust_var['current_block']
    
#     return cust_index_number


# def fn_cust_current_block_json(mobile_number:str,mast_tent_uuid:str):
#     result_data_dict = current_block_coll.find_one({"mobile_number":str(mobile_number),'tent_id':mast_tent_uuid})
#     if result_data_dict == None:
#         return None
#     del result_data_dict['_id'] 
#     return result_data_dict

# def str_to_list(string):
#     li = list(string.split(','))
#     return li
  
# @wa_json.post("/developer/integration/wa_json/send/{tent_id}", tags=["wa_json"], description="json whatsapp")
# async def whatsapp_json(tent_id:str, input_dict:Request):
#     try:
#         data = await input_dict.json()
#         json_dict=tent_wa_json(tent_id)
#         if json_dict is None:
#             return False
           
#         # private fn to replce matching words 
#         def __replace_match(match):
#             word = match.group(1)
#             if word in cust_block_json_dict:
#                 return cust_block_json_dict[word]
#             else:
#                 return match.group(0)
            
#         tent_json_blocks = json_dict['blocks']
#         tent_total_blocks_count = len(json_dict['blocks'])
#         cust_block_json_dict = fn_cust_current_block_json(mobile_number=str(data['from_number']),mast_tent_uuid=tent_id)
#         if cust_block_json_dict is None:
#             current_block_coll.insert_one({
#                 "cust_id": "qwerty12",
#                 "tent_id": f"{tent_id}",
#                 "mobile_number": f"{data['from_number']}",
#                 "is_interactive":False,
#                 "last_wamid":None,
#                 "total_blocks":tent_total_blocks_count,
#                 "current_block": 0,
#                 "wa_token":f"{json_dict['wa_token']}",
#                 "wa_version":f"{json_dict['wa_version']}",
#                 "wa_phone_id":f"{json_dict['wa_phone_id']}"
#             })
#             cust_block_json_dict = fn_cust_current_block_json(mobile_number=str(data['from_number']),mast_tent_uuid=tent_id)
#         cust_current_index_number = cust_block_json_dict['current_block']

#         if cust_current_index_number + 1 > tent_total_blocks_count:
#             return False
        
#         current_block_json = tent_json_blocks[cust_current_index_number]
#         # if current_block_json['type'] == 'text' and current_block_json['is_variable_appended'] == False:

#         if current_block_json['type'] == 'text':
#             print_text = re.sub(r'{{(.*?)}}', __replace_match, current_block_json['content']['children']['text'])

#             where = {"tent_id": tent_id,"mobile_number":str(data['from_number'])}
#             # if next_block_json['type'] == 'text':
#             newvalues = { "$set": {"current_block": cust_current_index_number + 1} }
#             current_block_coll.update_one(where, newvalues)

#             cust_variables = fn_cust_current_block_json(mobile_number=str(data['from_number']),mast_tent_uuid=tent_id)
#             send_wa_message(cust_variables,json_dict['wa_phone_id'],json_dict['wa_version'],json_dict['wa_token'],str(data['from_number']),print_text)
            
#         elif current_block_json['type'] == 'text_input':
            
#             where = {"tent_id": tent_id,"mobile_number":str(data['from_number'])}
#             newvalues = { "$set": {current_block_json['variable_name']: data['message'],"current_block": cust_current_index_number + 1}}
#             current_block_coll.update_one(where, newvalues)
            
#             if cust_current_index_number + 1 == tent_total_blocks_count:
#                 return False

#             if tent_json_blocks[cust_current_index_number + 1]['type'] == 'text':

#                 cust_block_json_dict = fn_cust_current_block_json(mobile_number=str(data['from_number']),mast_tent_uuid=tent_id)
#                 # caling private function "__replace_match" to replace string
#                 print_message = re.sub(r'{{(.*?)}}', __replace_match, tent_json_blocks[cust_current_index_number + 1]['content']['children']['text'])
                
#                 where = {"tent_id": tent_id,"mobile_number":str(data['from_number'])}
#                 newvalues = { "$set": {current_block_json['variable_name']: data['message'],"current_block": cust_block_json_dict['current_block'] + 1}}
#                 current_block_coll.update_one(where, newvalues)
#                 cust_variables = fn_cust_current_block_json(mobile_number=str(data['from_number']),mast_tent_uuid=tent_id)
#                 send_wa_message(cust_variables,json_dict['wa_phone_id'],json_dict['wa_version'],json_dict['wa_token'],str(data['from_number']),print_message)
#             elif tent_json_blocks[cust_current_index_number + 1]['type'] == 'Code':
#                 cust_block_json_dict = fn_cust_current_block_json(mobile_number=str(data['from_number']),mast_tent_uuid=tent_id)
#                 where = {"tent_id": tent_id,"mobile_number":str(data['from_number'])}
#                 newvalues = { "$set": {current_block_json['variable_name']: data['message'],"current_block": cust_block_json_dict['current_block'] + 1}}
#                 current_block_coll.update_one(where, newvalues)

#                 cust_current_index_number = cust_block_json_dict['current_block']
#                 if cust_current_index_number + 1 > tent_total_blocks_count:
#                     return False
#                 current_block_json = tent_json_blocks[cust_current_index_number]
#                 exec(current_block_json['options']['content'])
                
#                 cust_block_json_dict = fn_cust_current_block_json(mobile_number=str(data['from_number']),mast_tent_uuid=tent_id)     
#                 cust_current_index_number = cust_block_json_dict['current_block']
#                 all_blocks = tent_wa_json_block(mast_tent_uuid=tent_id)

#                 cust_block_json_dict = fn_cust_current_block_json(mobile_number=str(data['from_number']),mast_tent_uuid=tent_id)
#                 cust_current_index_number = cust_block_json_dict['current_block']
#                 if cust_current_index_number >= tent_total_blocks_count:
#                     return False
                
#                 latest_block = all_blocks[cust_current_index_number]
#                 if latest_block['type'] == 'Code':
#                     print_text = re.sub(r'{{(.*?)}}', __replace_match, latest_block['options']['content'])
#                     where = {"tent_id": tent_id,"mobile_number":str(data['from_number'])}
#                     newvalues = { "$set": {"current_block": cust_current_index_number + 1} }
#                     current_block_coll.update_one(where, newvalues)
#                     exec(latest_block['options']['content'])


#                 elif latest_block['type'] == 'text':
#                     print_text = re.sub(r'{{(.*?)}}', __replace_match, latest_block['content']['children']['text'])
#                     where = {"tent_id": tent_id,"mobile_number":str(data['from_number'])}
#                     newvalues = { "$set": {"current_block": cust_current_index_number + 1} }
#                     current_block_coll.update_one(where, newvalues)
#                     cust_variables = fn_cust_current_block_json(mobile_number=str(data['from_number']),mast_tent_uuid=tent_id)

#                     send_wa_message(cust_variables,json_dict['wa_phone_id'],json_dict['wa_version'],json_dict['wa_token'],str(data['from_number']),print_text)
#         elif current_block_json['type'] == 'consult':
#             print('*****************************8')
#             print_text = re.sub(r'{{(.*?)}}', __replace_match, current_block_json['content']['children']['text'])
#             where = {"tent_id": tent_id,"mobile_number":str(data['from_number'])}
#             newvalues = { "$set": {"current_block": cust_current_index_number + 1,"is_consult":True} }
#             current_block_coll.update_one(where, newvalues)

#             cust_variables = fn_cust_current_block_json(mobile_number=str(data['from_number']),mast_tent_uuid=tent_id)
#             # consult trigger via json bot
#             send_wa_message(cust_variables,json_dict['wa_phone_id'],json_dict['wa_version'],json_dict['wa_token'],str(data['from_number']),print_text)
#             # wa_support_chead_creation(from_number=str(data['from_number']),tent_id=tent_id,tent_user_id=None,cust_id=cust_variables.get("cust_id"),cust_name=cust_variables.get("cust_name"))
                
#         elif current_block_json['type'] == 'Code':

#             cust_block_json_dict = fn_cust_current_block_json(mobile_number=str(data['from_number']),mast_tent_uuid=tent_id)              
#             where = {"tent_id": tent_id,"mobile_number":str(data['from_number'])}
#             newvalues = { "$set": {current_block_json['variable_name']: data['message'],"current_block": cust_block_json_dict['current_block'] + 1}}
#             current_block_coll.update_one(where, newvalues)
#             cust_current_index_number = cust_block_json_dict['current_block']
#             if cust_current_index_number + 1 > tent_total_blocks_count:
#                 return False
#             current_block_json = tent_json_blocks[cust_current_index_number]
#             exec(current_block_json['options']['content'])

#         elif current_block_json['type'] == 'number_input':
#             where = {"tent_id": tent_id,"mobile_number":str(data['from_number'])}
#             newvalues = { "$set": {current_block_json['variable_name']: data['message'],"current_block": cust_current_index_number + 1}}
#             current_block_coll.update_one(where, newvalues)
            
#             if tent_json_blocks[cust_current_index_number + 1]['type'] == 'text':
#                 cust_block_json_dict = fn_cust_current_block_json(mobile_number=str(data['from_number']),mast_tent_uuid=tent_id)
#                 # caling private function "__replace_match" to replace string
#                 print_message = re.sub(r'{{(.*?)}}', __replace_match, tent_json_blocks[cust_current_index_number + 1]['content']['children']['text'])
                
#                 where = {"tent_id": tent_id,"mobile_number":str(data['from_number'])}
#                 newvalues = { "$set": {current_block_json['variable_name']: data['message'],"current_block": cust_block_json_dict['current_block'] + 1}}
#                 current_block_coll.update_one(where, newvalues)
                
#                 cust_variables = fn_cust_current_block_json(mobile_number=str(data['from_number']),mast_tent_uuid=tent_id)
#                 send_wa_message(cust_variables,json_dict['wa_phone_id'],json_dict['wa_version'],json_dict['wa_token'],str(data['from_number']),print_message)
#             elif tent_json_blocks[cust_current_index_number + 1]['type'] == 'Code':
#                 cust_block_json_dict = fn_cust_current_block_json(mobile_number=str(data['from_number']),mast_tent_uuid=tent_id)

#                 where = {"tent_id": tent_id,"mobile_number":str(data['from_number'])}
#                 newvalues = { "$set": {current_block_json['variable_name']: data['message'],"current_block": cust_block_json_dict['current_block'] + 1}}
#                 current_block_coll.update_one(where, newvalues)
#                 # exec(current_block_json['options']['content'])
#                 cust_current_index_number = cust_block_json_dict['current_block']
#                 if cust_current_index_number + 1 > tent_total_blocks_count:
#                     return False
#                 current_block_json = tent_json_blocks[cust_current_index_number]
#                 exec(current_block_json['options']['content'])
        
#         elif current_block_json['type'] == 'interactive':
#             print_text = re.sub(r'{{(.*?)}}', __replace_match, current_block_json['content']['children']['text'])
#             where = {"tent_id": tent_id,"mobile_number":str(data['from_number'])}
#             newvalues = { "$set": {"current_block": cust_current_index_number + 1} }
#             current_block_coll.update_one(where, newvalues)

#             cust_variables = fn_cust_current_block_json(mobile_number=str(data['from_number']),mast_tent_uuid=tent_id)
#             send_custom_interactive(variables=cust_variables,options=current_block_json['content']['children']['options'],text=print_text)
#         elif current_block_json['type'] == 'interactive_input':
#             where = {"tent_id": tent_id,"mobile_number":str(data['from_number'])}
#             newvalues = { "$set": {current_block_json['variable_name']: data['message'],"current_block": cust_current_index_number + 1}}
#             current_block_coll.update_one(where, newvalues)
#             if cust_current_index_number + 1 >= tent_total_blocks_count:
#                 return False
#             cust_current_block_json = fn_upcoming_block(mobile_number=str(data['from_number']),mast_tent_uuid=tent_id)
#             if cust_current_block_json['type'] == 'interactive':
#                 cust_current_index_num = fn_cust_index_number(mobile_number=str(data['from_number']),mast_tent_uuid=tent_id)
                
#                 where = {"tent_id": tent_id,"mobile_number":str(data['from_number'])}
#                 newvalues = { "$set": {"current_block": cust_current_index_num + 1} }
#                 current_block_coll.update_one(where, newvalues)

#                 print_text = re.sub(r'{{(.*?)}}', __replace_match, cust_current_block_json['content']['children']['text'])
#                 cust_variables = fn_cust_current_block_json(mobile_number=str(data['from_number']),mast_tent_uuid=tent_id)
#                 send_custom_interactive(variables=cust_variables,options=cust_current_block_json['content']['children']['options'],text=print_text)
            
#             elif cust_current_block_json['type'] == 'text':
#                 cust_current_index_num = fn_cust_index_number(mobile_number=str(data['from_number']),mast_tent_uuid=tent_id)
                
#                 where = {"tent_id": tent_id,"mobile_number":str(data['from_number'])}
#                 newvalues = { "$set": {"current_block": cust_current_index_num + 1} }
#                 current_block_coll.update_one(where, newvalues)

#                 print_text = re.sub(r'{{(.*?)}}', __replace_match, cust_current_block_json['content']['children']['text'])
#                 cust_variables = fn_cust_current_block_json(mobile_number=str(data['from_number']),mast_tent_uuid=tent_id)
#                 send_wa_message(cust_variables,json_dict['wa_phone_id'],json_dict['wa_version'],json_dict['wa_token'],str(data['from_number']),print_text)
#             elif cust_current_block_json['type'] == 'consult':

#                 print("***************************")
#                 cust_current_index_num = fn_cust_index_number(mobile_number=str(data['from_number']),mast_tent_uuid=tent_id)
                
#                 where = {"tent_id": tent_id,"mobile_number":str(data['from_number'])}
#                 newvalues = { "$set": {"current_block": cust_current_index_num + 1} }
#                 current_block_coll.update_one(where, newvalues)

#                 print_text = re.sub(r'{{(.*?)}}', __replace_match, cust_current_block_json['content']['children']['text'])
#                 cust_variables = fn_cust_current_block_json(mobile_number=str(data['from_number']),mast_tent_uuid=tent_id)
#                 send_wa_message(cust_variables,json_dict['wa_phone_id'],json_dict['wa_version'],json_dict['wa_token'],str(data['from_number']),print_text)
#                 # wa_support_chead_creation(from_number=str(data['from_number']),tent_id=tent_id,tent_user_id=None,cust_id=cust_variables.get("cust_id"),cust_name=cust_variables.get("cust_name"))
            
#         return tent_json_blocks

#     except ValueError:
#         raise HTTPException(status_code=404, detail="err_jsonValueError")

