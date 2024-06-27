# import requests
# from fastapi import HTTPException
# from dotenv import load_dotenv
# import os
# import json
# from models.common import update_user_status
# from utils.aes import AESCipher
# from pymongo import MongoClient
# from pymongo.errors import ConnectionFailure
# import pytz
# from datetime import datetime

# timezone = pytz.timezone('Asia/Kolkata')


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
# current_block_coll=db_name["cust_current_block"]
# wa_chat_history_coll=db_name['wa_chat_history']
# wa_api_response=db_name['wa_api_response']

# list_of_flows = [{"id":'product',"title":"Product info"}, {"id":'order',"title":"Place order"}, {"id":'payment',"title":"Payment"}, {"id":'track_order', "title":"Track my Order"}, {"id":'sample_coll', "title":"Sample collection"}, {"id":'reporting', "title":"Reporting and result"}, {"id":'consultation', "title":"Consultation"}, {"id":'discounts', "title":"Promotions and discounts"}, {"id":'cust_service', "title":"Customer Service"} ]


# def get_tent_product_list(variables:dict):
#     headers = {
#         'Internal' : 'LYFnGO'
#     }
#     url = f"{lyfngo_service_url}products/get/productListByTentUuid/{variables['tent_id']}"
#     response = requests.request("GET", url, headers=headers, data="")
#     if response.status_code == 200:
#         response_data = json.loads(response.text)
#         interactive = response_data.get('data')
#         rows =[]
#         if interactive != None:
#             if len(interactive) > 3:
#                 for i in interactive:
#                     title = i['langCode'][:24] if len(i['languageName'][:24]) == 0 else i['languageName'][:24]
#                     row = {
#                             "id": f"{i['langCode']}",
#                             "title": f"{title}",
#                             "description": f"{title}"
#                         }
#                     rows.append(row)
#                 result = wa_list_send_api(variables=variables, interactive_headers={"header":'',"footer":'',"body":"Select Your Language","button_name":"Language List",'title':"Select any one Language"}, interactive_list=rows)
#             elif len(interactive) <= 3:
#                 for i in interactive:
#                     title = i['langCode'][:24] if len(i['languageName'][:24]) == 0 else i['languageName'][:24]

#                     row = {
#                         "type": "reply",
#                         "reply": {
#                             "id": f"{i['langCode']}",
#                             "title": f"{title}",
#                         }
#                     }
#                     rows.append(row)
#                 result = wa_buttons_send_api(variables=variables, interactive_headers={"header":'',"footer":'',"body":"Select Your Language","button_name":"Language List",'title':"Select any one Language"}, interactive_list=rows)
#             return result
#     return False


# def get_language_list(variables:dict):
#     headers = {
#         'Internal' : 'LYFnGO'
#     }
#     url = lyfngo_service_url+f"ms-communication/lookup/tentLanguages?tentId={variables['tent_id']}"

#     response = requests.request("GET", url, headers=headers, data="")

#     if response.status_code == 200:
#         response_data = json.loads(response.text)
#         interactive = response_data.get('data')
#         rows =[]
#         if interactive != None:
#             if len(interactive) > 3:
#                 for i in interactive:
#                     title = i['langCode'][:24] if len(i['languageName'][:24]) == 0 else i['languageName'][:24]
#                     row = {
#                             "id": f"{i['langCode']}",
#                             "title": f"{title}",
#                             "description": f"{title}"
#                         }
#                     rows.append(row)
#                 result = wa_list_send_api(variables=variables, interactive_headers={"header":'',"footer":'',"body":"Select Your Language","button_name":"Language List",'title':"Select any one Language"}, interactive_list=rows)
#             elif len(interactive) <= 3:
#                 for i in interactive:
#                     title = i['langCode'][:24] if len(i['languageName'][:24]) == 0 else i['languageName'][:24]

#                     row = {
#                         "type": "reply",
#                         "reply": {
#                             "id": f"{i['langCode']}",
#                             "title": f"{title}",
#                         }
#                     }
#                     rows.append(row)
#                 result = wa_buttons_send_api(variables=variables, interactive_headers={"header":'',"footer":'',"body":"Select Your Language","button_name":"Language List",'title':"Select any one Language"}, interactive_list=rows)
#             return result
#     return False

# def load_customised_templates(variables:dict):
#     headers = {
#         'Internal' : 'LYFnGO'
#     }
#     tempates_url = lyfngo_service_url+f"communication/fetchcutomizedtemplete/{variables['tent_id']}/{variables['language']}"
#     templates_response = requests.request("GET", tempates_url, headers=headers, data="")
#     if templates_response.status_code == 200:
#         templates_data = templates_response.json().get('data')
#         for i in templates_data:
#             update_data = {
#                 i['mastCommName']:i['actualCommContent'] if i['tentCommContent'] == None else i['tentCommContent']
#             }
#             where = {"tent_id": variables['tent_id'],"mobile_number":variables['mobile_number']}
#             newvalues = { "$set": update_data}
#             current_block_coll.update_one(where, newvalues)
#     return True
# def get_group_list(variables:dict)->dict:
#     url = f"{lyfngo_service_url}ms-communication/tentGroupList/index"
#     payload = {}
#     headers = {
#     'Internal': 'LYFnGO'
#     }
#     response = requests.request("GET", url, headers=headers, data=payload)
#     if response.status_code == 200:    
#         response_data = response.json()
#         interactive = response_data.get('data')
#         rows =[]
#         if interactive != None:
#             if len(interactive) > 3:
#                 for i in interactive:
#                     row = {
#                             "id": f"{i['mastTentGroupUuid']}",
#                             "title": f"{i['mastTentGroupName'][:24]}",
#                             "description": f"{i['mastTentGroupDesc']}"
#                         }
#                     rows.append(row)
#                 result = wa_list_send_api(variables=variables, interactive_headers={"header":'',"footer":'',"body":"Select any one Groups","button_name":"Groups List",'title':"Select any one group"}, interactive_list=rows)
#             elif len(interactive) <= 3:
#                 for i in interactive:
#                     row = {
#                         "type": "reply",
#                         "reply": {
#                             "id": f"{i['mastTentGroupUuid']}",
#                             "title": f"{i['mastTentGroupName'][:24]}"
#                         }
#                     }
#                     rows.append(row)
#                 result = wa_buttons_send_api(variables=variables, interactive_headers={"header":'',"footer":'',"body":"Select any one Groups","button_name":"Groups List",'title':"Select any one group"}, interactive_list=rows)
#             return result
#     return False


# def flows_list(variables:dict)->dict:

#     interactive = list_of_flows
#     rows =[]
#     if interactive != None:
#         if len(interactive) > 3:
#             for i in interactive:
#                 row = {
#                         "id": f"{i['id']}",
#                         "title": f"{i['title'][:24]}",
#                         "description": f"{i['title']}"
#                     }
#                 rows.append(row)
#             result = wa_list_send_api(variables=variables, interactive_headers={"header":'',"footer":'',"body":"Select any one from list","button_name":"Flows List",'title':"Select any one from list"}, interactive_list=rows)
#         elif len(interactive) <= 3:
#             for i in interactive:
#                 row = {
#                     "type": "reply",
#                     "reply": {
#                         "id": f"{i['id']}",
#                         "title": f"{i['title'][:24]}"
#                     }
#                 }
#                 rows.append(row)
#             result = wa_buttons_send_api(variables=variables, interactive_headers={"header":'',"footer":'',"body":"Select any one from list","button_name":"Flows List",'title':"Select any one from list"}, interactive_list=rows)
#         return result

# def get_tent_type_list(variables:dict)->dict:
#     url = f"{lyfngo_service_url}ms-communication/tentType/get/mastTentGroupId/{variables['group_id']}"
#     payload = {}
#     headers = {
#     'Internal': 'LYFnGO'
#     }
#     response = requests.request("GET", url, headers=headers, data=payload)
#     if response.status_code == 200:    
#         response_data = response.json()
#         interactive = response_data.get('data')
#         rows =[]
#         if interactive != None:
#             if len(interactive) > 3:
#                 for i in interactive:
#                     row = {
#                             "id": f"{i['mastTtypeUuid']}",
#                             "title": f"{i['mastTentTypeName'][:24]}",
#                             "description": f"{i['mastTentTypeName']}"
#                         }
#                     rows.append(row)
#                 result = wa_list_send_api(variables=variables, interactive_headers={"header":'',"footer":'',"body":"Select any one Tent Type","button_name":"Tent Type List",'title':"Select any one Tent Type"}, interactive_list=rows)
#             elif len(interactive) <= 3:
#                 for i in interactive:
#                     row = {
#                         "type": "reply",
#                         "reply": {
#                             "id": f"{i['mastTtypeUuid']}",
#                             "title": f"{i['mastTentTypeName'][:24]}"
#                         }
#                     }
#                     rows.append(row)
#                 result = wa_buttons_send_api(variables=variables, interactive_headers={"header":'',"footer":'',"body":"Select any one Tent Type","button_name":"Tent Type List",'title':"Select any one Tent Type"}, interactive_list=rows)
#             return result
#     return False



# def get_speciality_list(variables:dict)->dict:
#     url = f"{lyfngo_service_url}ms-communication/lookup/SpecialityType/tentTypeId/{variables['tent_type_id']}"
#     payload = {}
#     headers = {
#     'Internal': 'LYFnGO'
#     }
#     response = requests.request("GET", url, headers=headers, data=payload)
#     if response.status_code == 200:    
#         response_data = response.json()

#         interactive = response_data.get('data')
#         rows =[]
#         if interactive != None:
#             if len(interactive) > 3:
#                 for i in interactive:
#                     row = {
#                             "id": f"{i['specialityUuid']}",
#                             "title": f"{i['specialityName'][:24]}",
#                             "description": f"{i['specialityName']}"
#                         }
#                     rows.append(row)
#                 result = wa_list_send_api(variables=variables, interactive_headers={"header":'',"footer":'',"body":"Select any one Speciality","button_name":"Speciality List",'title':"Select any one Speciality"}, interactive_list=rows)
#             elif len(interactive) <= 3:
#                 for i in interactive:
#                     row = {
#                         "type": "reply",
#                         "reply": {
#                             "id": f"{i['specialityUuid']}",
#                             "title": f"{i['specialityName'][:24]}"
#                         }
#                     }
#                     rows.append(row)
#                 result = wa_buttons_send_api(variables=variables, interactive_headers={"header":'',"footer":'',"body":"Select any one Speciality","button_name":"Speciality List",'title':"Select any one Speciality"}, interactive_list=rows)
#             return result
#     return False



# def get_lyfngo_countries_list(variables:dict)->dict:
#     url = f"{lyfngo_service_url}communication/subscriptioncountries/fetch"
#     payload = {}
#     headers = {
#     'Internal': 'LYFnGO'
#     }
#     response = requests.request("GET", url, headers=headers, data=payload)
#     if response.status_code == 200:    
#         response_data = response.json()

#         interactive = response_data.get('data')
#         rows =[]
#         if interactive != None:
#             if len(interactive) > 3:
#                 for i in interactive:
#                     row = {
#                             "id": f"{i['countryNameAbbreviation']}",
#                             "title": f"{i['countryName'][:24]}",
#                             "description": f"{i['countryName']}"
#                         }
#                     rows.append(row)
#                 result = wa_list_send_api(variables=variables, interactive_headers={"header":'',"footer":'',"body":"Select any one Country","button_name":"Country List",'title':"Select any one Country"}, interactive_list=rows)
#             elif len(interactive) <= 3:
#                 for i in interactive:
#                     row = {
#                         "type": "reply",
#                         "reply": {
#                             "id": f"{i['countryNameAbbreviation']}",
#                             "title": f"{i['countryName'][:24]}"
#                         }
#                     }
#                     rows.append(row)
#                 result = wa_buttons_send_api(variables=variables, interactive_headers={"header":'',"footer":'',"body":"Select any one Country","button_name":"Country List",'title':"Select any one Country"}, interactive_list=rows)
#             return result
#     return False




# def get_lyfngo_states_list(variables:dict)->dict:
#     url = f"{lyfngo_service_url}ms-communication/lookup/citiesStates/mast_country_code/{variables['country_id']}"
#     payload = {}
#     headers = {
#     'Internal': 'LYFnGO'
#     }
#     response = requests.request("GET", url, headers=headers, data=payload)
#     if response.status_code == 200:    
#         response_data = response.json()

#         interactive = response_data.get('data')
#         rows =[]
#         if interactive != None:
#             if len(interactive) > 3:
#                 for i in interactive:
#                     row = {
#                             "id": f"{i['mastState']}",
#                             "title": f"{i['mastState'][:24]}",
#                             "description": f"{i['mastState']}"
#                         }
#                     rows.append(row)
#                 result = wa_list_send_api(variables=variables, interactive_headers={"header":'',"footer":'',"body":"Select any one State","button_name":"State List",'title':"Select any one State"}, interactive_list=rows)
#             elif len(interactive) <= 3:
#                 for i in interactive:
#                     row = {
#                         "type": "reply",
#                         "reply": {
#                             "id": f"{i['mastState']}",
#                             "title": f"{i['mastState'][:24]}"
#                         }
#                     }
#                     rows.append(row)
#                 result = wa_buttons_send_api(variables=variables, interactive_headers={"header":'',"footer":'',"body":"Select any one State","button_name":"State List",'title':"Select any one State"}, interactive_list=rows)
#             return result
#     return False


# def tent_registration(variable):
#     avl_data = avl()
#     country_name = country_code =''
#     for i in avl_data:
#         if i['countryCode'] == variable['country_id']:
#             country_name = i['country']
#             country_code = f"{i['mastLookupKey']}"
#             break

#     payload = json.dumps({
#         "email": variable['email'],
#         "mobileNo": variable['mobile_number'],
#         "countryCode": f"{country_code}",
#         "userType": "TNT",
#         "password": "Welcome@123",
#         "isSignUp": True,
#         "isActivate": False,
#         "mandatory": True
#     })

#     headers = {
#         'Internal': 'LYFnGO',
#         'Content-Type': 'application/json'
#     }
#     url = f"{lyfngo_service_url}users/auth/signup"
#     response = requests.request("POST", url, headers=headers, data=payload)

#     if response.status_code == 200:
#         identityUuid = response.json().get("data").get('identityUuid')
#         bearerData = json.dumps({
#             'otpNumber':response.json().get("data").get('otp'),
#             'userType':"TNT",
#             'uuid':response.json().get("data").get('identityUuid'),
#             'isExpired':False
#         })
#         headers = {
#             'Internal': 'LYFnGO',
#             'Content-Type': 'application/json'
#         }
#         url = f"{lyfngo_service_url}users/auth/v2/validateOTP"
#         response = requests.request("POST", url, headers=headers, data=bearerData)
#         if response.status_code == 200:
#             bearerToken = response.json().get('data').get('Bearer')
#             tentData =  json.dumps({
#                 "mastTentTypeUuid" :f"{variable['tent_type_id']}",
#                 "tentCountryCode" : f"{country_code}",
#                 "tentUserIdentityUuid":f"{identityUuid}",
#                 "userType": "TNT",
#                 "tentStatus":True,
#                 "tentName": f"{variable['tent_name']}",
#                 "tentEmail" :f"{variable['email']}",
#                 "isAddress" : True,
#                 "country" : f"{country_name}",
#                 "state" : f"{variable['state_name']}",
#                 "specialityUuid" : f"{variable['speciality_id']}",
#                 "createDemo" : False,
#                 "duplicate": "both",
#                 "countryAbbrev":f"{variable['country_id']}",
#                 "tentCommLanguage":f"en"
#             })
#             headers={
#                 'Internal': 'LYFnGO',
#                 'Content-Type': 'application/json',
#                 'Authorization': f'Bearer {bearerToken}',
#             }
#             url = f"{lyfngo_service_url}users/tenantMaster/v2/saveTenantMaster/{identityUuid}"
#             response = requests.request("POST", url, headers=headers, data=tentData)
#             print(response.text)

# def avl()->dict:
#     url = f"{lyfngo_service_url}communication/mobile_codes"
#     payload = {}
#     headers = {
#         'Internal': 'LYFnGO'
#     }
#     response = requests.request("GET", url, headers=headers, data=payload)
#     if response.status_code == 200:
#         data = response.json()
#         return data['data']
#     return []

# def wa_list_send_api(variables:dict, interactive_headers:dict, interactive_list:list)->dict:

#     url = f"https://graph.facebook.com/v{variables['wa_version']}/{variables['wa_phone_id']}/messages"
#     payload = json.dumps({
#         "messaging_product": "whatsapp",
#         "recipient_type": "individual",
#         "to": f"{variables['mobile_number']}",
#         "type": "interactive",
#         "interactive": {
#             "type": "list",
#             "header": {
#                 "type": "text",
#                 "text": f"{interactive_headers['header']}"
#             },
#             "body": {
#                 "text": f"{interactive_headers['body']}"
#             },
#             "footer": {
#                 "text": f"{interactive_headers['footer']}"
#             },
#             "action": {
#                 "button": f"{interactive_headers['button_name']}",
#                 "sections": [
#                     {
#                         "title": f"{interactive_headers['title'][:24]}",
#                         "rows": interactive_list[:10]
#                     }
#                 ]
#             }
#         }
#     })
#     headers = {
#         'Content-Type': 'application/json',
#         'Authorization': f"Bearer {variables['wa_token']}"
#     }
#     response = requests.request("POST", url, headers=headers, data=payload)
#     data = response.json()
#     current_date = datetime.now(timezone)
#     wa_api_response.insert_one({"url":url,"accesstoken":variables['wa_token'],'api_status_code':response.status_code,"data":data,"created_on":current_date})

#     if response.status_code == 200:
#         wamid = data['messages'][0]['id'] if data.get('messages') != None and len(data['messages']) > 0 and 'id' in data['messages'][0] else None
#         current_block_coll.update_one({"mobile_number":variables['mobile_number'],'tent_id':variables['tent_id']}, {"$set":{"last_wamid":wamid,"type":'list_reply',"is_interactive":True}})
#         wa_chat_history_coll.insert_one({"user_initiated":False,"from_number":variables['mobile_number'],'tent_id':variables['tent_id'],'message':interactive_headers['body'],'wamid':wamid,"created_on":current_date})
#     return True



# def wa_buttons_send_api(variables:dict, interactive_headers:dict, interactive_list:list)->dict:

#     url = f"https://graph.facebook.com/v{variables['wa_version']}/{variables['wa_phone_id']}/messages"

#     payload = json.dumps({
#         "messaging_product": "whatsapp",
#         "recipient_type": "individual",
#         "to": f"{variables['mobile_number']}",
#         "type": "interactive",
#         "interactive": {
#             "type": "button",
#             "body": {
#                 "text": f"{interactive_headers['body']}"
#             },
#             "action": {
#                 "buttons": interactive_list[:10]
#             }
#         }
#     })
#     headers = {
#         'Content-Type': 'application/json',
#         'Authorization': f"Bearer {variables['wa_token']}"
#     }
#     response = requests.request("POST", url, headers=headers, data=payload)
#     data = response.json()

#     current_date = datetime.now(timezone)
#     wa_api_response.insert_one({"url":url,"accesstoken":variables['wa_token'],'api_status_code':response.status_code,"data":data,"created_on":current_date})

#     if response.status_code == 200:
#         wamid = data['messages'][0]['id'] if data.get('messages') != None and len(data['messages']) > 0 and 'id' in data['messages'][0] else None
#         current_block_coll.update_one({"mobile_number":variables['mobile_number'],'tent_id':variables['tent_id']}, {"$set":{"last_wamid":wamid,"type":'button_reply',"is_interactive":True}})
#         wa_chat_history_coll.insert_one({"user_initiated":False,"from_number":variables['mobile_number'],'tent_id':variables['tent_id'],'message':interactive_headers['body'],'wamid':wamid,"created_on":current_date})
    
#     return True

# def send_custom_interactive(variables:dict,options:list,text:str)->dict:
#     interactive = options
#     rows =[]
#     if interactive != None:
#         if len(interactive) > 3:
#             for i in interactive:
#                 row = {
#                         "id": f"{i['id']}",
#                         "title": f"{i['title'][:24]}",
#                         "description": f"{i['desc']}"
#                     }
#                 rows.append(row)
#             result = wa_list_send_api(variables=variables, interactive_headers={"header":'',"footer":'',"body":text,"button_name":"List",'title':"Choose any one"}, interactive_list=rows)
#         elif len(interactive) <= 3:
#             for i in interactive:
#                 row = {
#                     "type": "reply",
#                     "reply": {
#                         "id": f"{i['id']}",
#                         "title": f"{i['title'][:24]}"
#                     }
#                 }
#                 rows.append(row)
#             result = wa_buttons_send_api(variables=variables, interactive_headers={"header":'',"footer":'',"body":text,"button_name":"List",'title':"Select any one"}, interactive_list=rows)
#         return result
#     return True