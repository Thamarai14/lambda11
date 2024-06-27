# import json
# import requests
# import os
# from dotenv import load_dotenv
# from pymongo import MongoClient
# from pymongo.errors import ConnectionFailure
# from fastapi import HTTPException

# import pytz
# from datetime import datetime


# load_dotenv()
# lyfngo_service_url = os.getenv("LYFNGO_SERVICE_URL")
# application_name =os.getenv("APPLICATION_NAME")
# aes_secret_key = os.getenv("AES_SECRET_KEY")
# mongo_db_url = os.getenv("MONGO_DB_URL")
# # Connecting to the database and creating a collection.
# try:
#     cluster = MongoClient(mongo_db_url)
# except ConnectionFailure:
#     raise HTTPException(status_code=404, detail="err_mongo_connection")
# db_name = cluster["json_bot"]
# wa_chat_history_coll = db_name['wa_chat_history']
# wa_api_response=db_name['wa_api_response']
# current_block_coll=db_name["cust_current_block"]


# timezone = pytz.timezone('Asia/Kolkata')

# def send_wa_message(cust_variables,phone_number_id:str, wa_version:str, token:str, to:str, message:str)->dict:
#     url = f"https://graph.facebook.com/v{wa_version}/{phone_number_id}/messages"
#     payload = json.dumps({
#         "messaging_product": "whatsapp",
#         "recipient_type": "individual",
#         "to": f"{to}",
#         "type": "text",
#         "text": {
#             "preview_url": False,
#             "body": f"{message}"
#         }
#     })
#     headers = {
#         'Content-Type': 'application/json',
#         'Authorization': f'Bearer {token}'
#     }
#     response = requests.request("POST", url, headers=headers, data=payload)
#     data = response.json()
#     current_date = datetime.now(timezone)
#     wa_api_response.insert_one({"url":url,"accesstoken":token,'api_status_code':response.status_code,"data":data,"created_on":current_date})

#     if response.status_code == 200:
#         wamid = data['messages'][0]['id'] if data.get('messages') != None and len(data['messages']) > 0 and 'id' in data['messages'][0] else None
#         current_block_coll.update_one({"mobile_number":to,'tent_id':cust_variables['tent_id']}, {"$set":{"last_wamid":wamid,"type":'list_reply',"is_interactive":False}})
#         wa_chat_history_coll.insert_one({"user_initiated":False,"from_number":to,'tent_id':cust_variables['tent_id'],'message':message,'wamid':wamid,"created_on":current_date})
#     # if status == False:
#     #     wa_resp_id = response_data.get('messages').get([0]).get('id')
#     return data


# # def send_wa_failure_message(phone_number_id:str, wa_version:str, token:str, to:str, message:str)->dict:
# #     url = f"https://graph.facebook.com/v{wa_version}/{phone_number_id}/messages"
# #     payload = json.dumps({
# #         "messaging_product": "whatsapp",
# #         "recipient_type": "individual",
# #         "to": f"{to}",
# #         "type": "text",
# #         "text": {
# #             "preview_url": False,
# #             "body": f"{message}"
# #         }
# #     })
# #     headers = {
# #         'Content-Type': 'application/json',
# #         'Authorization': f'Bearer {token}'
# #     }
# #     response = requests.request("POST", url, headers=headers, data=payload)
# #     return response.json()