from fastapi import FastAPI, HTTPException,Depends,Request,Path, Response
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlmodel import SQLModel, Field
from typing import Optional 
from datetime import date, datetime, time
from enum import Enum
from utils.apicalllog import request_session, templeted_log_insert
import json
from dotenv import load_dotenv
import os
from auth.jwt_bearer import JWTBearer
from Controllers.registration import registration_router
# from Controllers.wa_json_controller import wa_json
from models.common import validate_token_developer_id, validate_api, get_customer_list_by_tent_id, find_tent_master_by_developer_id,get_tenant_integeration_config, wooc_id_update_to_customer, get_customer_by_attrs,get_customer_by_wooc_id,get_product_by_wooc_id,zoho_crm_history,wa_template_messages_get,wa_opt_out_check, TemplatePatten
from woocommerce import API
from starlette.exceptions import HTTPException as StarletteHTTPException
import json
from pydantic import EmailStr
from utils.aes import AESCipher
from woocommerce import API
from models.Integration_models import get_old_propery_integeration
from fastapi.exceptions import RequestValidationError
from utils.custom_logg import MyLogger
from typing import Callable, List, Union
from fastapi.routing import APIRoute
from mangum import Mangum

load_dotenv()
requests = request_session()
aes_secret_key = os.getenv("AES_SECRET_KEY")
sales_contact_number = os.getenv("SALES_CONTACT_NUMBER")


wa_lyfngo_phone_id = os.getenv("WA_LYFNGO_PHONE_ID")
wa_lyfngo_token = os.getenv("WA_LYFNGO_TOKEN")
wa_lyfngo_busienss_account_id = os.getenv("WA_LYFNGO_BUSSINESS_ACCOUNT_ID")

lyfngo_services_url = os.getenv("LYFNGO_SERVICE_URL")
MyLogger = MyLogger()



app = FastAPI(
    docs_url="/developer/integration/docs",
    redoc_url="/developer/integration/redocs",
    title="LYFnGO API Integeration",
    description="LYFnGO Developer Account",
    openapi_url="/developer/integration/openapi.json"
)

app.include_router(registration_router)

# app.include_router(wa_json)

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    MyLogger.log_error(f"Response:f{str(exc.detail)}")
    MyLogger.log_debug("************************fastapi request end*********************************")
    return JSONResponse(status_code=exc.status_code, content=jsonable_encoder({"status":False,"data":{}, "message":f"{str(exc.detail)}"}))

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    MyLogger.log_error(f"Response:{str(exc.errors())}")
    MyLogger.log_debug("************************fastapi request end*********************************")
    return JSONResponse(
        status_code=400,
        content=jsonable_encoder({"message": "err_Invalid_request", "data":exc.errors(), "status":False}),
    )
    
    
class log_stuff(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            MyLogger.log_debug("************************fastapi request start*********************************")
            req = await request.body()
            MyLogger.log_info(f"Request:{str(req)}")
            response: Response = await original_route_handler(request)
            MyLogger.log_info(f"Response:{str(response.body)}")
            MyLogger.log_debug("************************fastapi request end*********************************")
            return response

        return custom_route_handler
    
app.router.route_class = log_stuff

handler = Mangum(app)
 
class appointment_modes(str, Enum):
    online = "online"
    direct = "in-person"
    homeservice = "home"
class allowed_isp(str, Enum):
    active_rnr = "active_rnr"
    active_rnr_followup_one = "active_rnr_followup_one"
    active_rnr_followup_two = "active_rnr_followup_two"
    new_lead = "new_lead"

class book_appointments(SQLModel):
    userId: Optional[str] = Field(min_length=5, max_length=8)
    cutomerId: str = Field(min_length=5, max_length=8)
    date: date
    customerMailNotify: bool = Field(default=True)
    tentMailNotify: bool = Field(default=True)
    time: time
    durationInMins: int = Field(gt=14, le=121)
    appointmentModes: appointment_modes
    appointmentPrice: int

    class Config:
        schema_extra = {
            "example": {
                "userId": "DOCTOR ADMIN USER ID",
                "cutomerId": "CLIENT OR CUSTOMER ID",
                "date": "2023-05-11",
                "time": "11:30:00",
                "customerMailNotify": True,
                "tentMailNotify": True,
                "durationInMins": 15,
                "appointmentModes": "online",
                "appointmentPrice":100
            }
        }
        
class add_appointment_details(SQLModel):
    date: date
    class Config:
        schema_extra = {
            "example": {
                "date": "2023-05-11"
            }
        }

class add_customer(SQLModel):
    customer_name: str
    mobile_number: int
    dial_code:int
    customer_email: EmailStr

    class Config:
        schema_extra = {
            "example": {
                "customer_name": "john",
                "mobile_number": 1234567890,
                "dial_code":91,
                "customer_email":"john@example.com"
            }
        }
def patient_creation(data:dict):
    headers = {
        'Internal': 'LYFnGO'
    }
    url = lyfngo_services_url+f"users/customer/getPatientid/{data['mast_tent_uuid']}"

    response = requests.request("GET", url, headers=headers, data="")
    if response.status_code != 200:
        return None
    iv = response.headers.get('key')
    response_text = response.text

    aesObj = AESCipher(aes_secret_key.encode())
    dec_value = aesObj.decrypt(response_text,iv.encode())
    patient_id_json = json.loads(dec_value)


    client_dict = {
        "custName": data['customer_name'],
        "custCustomId": patient_id_json['data'],
        "custEmail": data['email'],
        "custCountryCode": f"+{data['dail_code']}",
        "custMobileNo": str(data['mobile_number']),
        "custMobileNotification": False,
        "custEmailNotification": False,
        "isAddress": False,
        "sourceFrom":"woocommerce"
    }
    encrypted_json_text =  json.dumps(client_dict)
    value = aesObj.encrypt(encrypted_json_text.encode(),iv.encode())

    payload = {
        "data":value.decode()
    }

    headers = {
        'Internal': 'LYFnGO',
        'Content-Type': 'application/json',
        "Key":iv
    }
    url = lyfngo_services_url+f"users/customer/saveCustomerMaster/{data['mast_tent_uuid']}"
    response = requests.request(
        "POST", url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        iv = response.headers.get('key')
        dec_value = aesObj.decrypt(response.text,iv.encode())
        cust_uuid = json.loads(dec_value).get('data').get('custUuid')
        # print(data.get("woocommerce_id"))
        wooc_id_update_to_customer(cust_uuid=cust_uuid,woocommerce_id=int(data['woocommerce_id']))
    return None

@app.post("/developer/integration/bookappointment/{developer_id}",dependencies=[Depends(JWTBearer())], tags=['Appointments'], description="Appointment creation")
async def bookappointment(input_data: book_appointments ,developer_id :str | None = Path(min_length= 5,max_length=16), token: str = Depends(JWTBearer())):
    
    tent_data = find_tent_master_by_developer_id(developer_id)
    token_valid = validate_token_developer_id(developer_id,token)
    if token_valid == None:
        json_compatible_item_data = jsonable_encoder({"status":False, "message": "err_forbidden", "data":[]})
        return JSONResponse(content=json_compatible_item_data,status_code=403)
    
    allowed_api_list = validate_api(token_valid.tent_id, '/developer/integration/bookappointment')
    if not allowed_api_list:
        json_compatible_item_data = jsonable_encoder({"status":False, "message": "err_forbidden", "data":[]})
        return JSONResponse(content=json_compatible_item_data,status_code=403)
    input_dict = input_data.__dict__
    mode_to_x = {'online': 1, 'in-person': 0}

    payload_json = {}
    payload_json['tentId'] = tent_data.tbl_tent_master.mast_tent_uuid
    payload_json['tentUserId'] = input_dict['userId']
    payload_json['custId'] = input_dict['cutomerId']
    payload_json['scheduledOn'] = str(input_dict['date'])
    payload_json['scheduledTime'] = str(
        input_dict['time'].replace(tzinfo=None))+'+05:30'
    payload_json['scheduledPeriod'] = input_dict['durationInMins']
    payload_json['onOff'] = mode_to_x.get(input_dict['appointmentModes'], 2)
    payload_json['custMail'] = input_dict['customerMailNotify']
    payload_json['tentMail'] = input_dict['tentMailNotify']
    payload_json['scheduledPeriodType'] = "Mins"
    payload_json['notes'] = ""
    payload_json['plannedProcedure'] = []
    payload_json['totalAppointmentPrice'] = str(input_dict['appointmentPrice'])
    payload_json['appointmentSource'] = "b2bflash"

    headers = {
        'Internal': 'LYFnGO',
        'Content-Type': 'application/json'
    }

    url = lyfngo_services_url+"ms-calendar-appointment/appointment/add"
    response = requests.request(
        "POST", url, headers=headers, data=json.dumps(payload_json))
    return JSONResponse(content=response.json(), status_code=response.status_code)

@app.post("/developer/integration/addAppointmentDetails/{developer_id}",dependencies=[Depends(JWTBearer())], tags=['Appointments'], description="get calendar details")
async def fn_add_appointment_details(input_data: add_appointment_details, developer_id :str | None = Path(min_length= 5,max_length=16), token: str = Depends(JWTBearer())):
    token_valid = validate_token_developer_id(developer_id,token)
    if token_valid == None:
        json_compatible_item_data = jsonable_encoder({"status":False, "message": "err_forbidden", "data":[]})
        return JSONResponse(content=json_compatible_item_data,status_code=403)

    tent_data = find_tent_master_by_developer_id(developer_id)

    allowed_api_list = validate_api(token_valid.tent_id, '/developer/integration/addAppointmentDetails')
    if not allowed_api_list:
        json_compatible_item_data = jsonable_encoder({"status":False, "message": "err_forbidden", "data":[]})
        return JSONResponse(content=json_compatible_item_data,status_code=403)
    input_dict = input_data.__dict__
    headers = {
        'Internal': 'LYFnGO',
        'Content-Type': 'application/json'
    }
    url = lyfngo_services_url+f"ms-calendar-appointment/consilidate/addAppointmentfetch?tentId={tent_data.tbl_tent_master.mast_tent_uuid}&scheduledOn={input_dict['date']}"
    response = requests.request("GET", url, headers=headers, data="")
    return JSONResponse(content=response.json(), status_code=response.status_code)

@app.get("/developer/integration/productList/{developer_id}",dependencies=[Depends(JWTBearer())], tags=['Products'], description="get product list")
async def get_product_list(developer_id :str | None = Path(min_length= 5,max_length=16), token: str = Depends(JWTBearer())):
    token_valid = validate_token_developer_id(developer_id,token)
    if token_valid == None:
        json_compatible_item_data = jsonable_encoder({"status":False, "message": "err_forbidden", "data":[]})
        return JSONResponse(content=json_compatible_item_data,status_code=403)
    tent_data = find_tent_master_by_developer_id(developer_id)

    allowed_api_list = validate_api(token_valid.tent_id, '/developer/integration/productList')
    if not allowed_api_list:
        json_compatible_item_data = jsonable_encoder({"status":False, "message": "err_forbidden", "data":[]})
        return JSONResponse(content=json_compatible_item_data,status_code=403)
    headers = {
        'Internal': 'LYFnGO',
        'Content-Type': 'application/json'
    }
    url = lyfngo_services_url+f"products/get/productListByTentUuid/{tent_data.tbl_tent_master.mast_tent_uuid}"
    response = requests.request("GET", url, headers=headers, data="")
    return JSONResponse(content=response.json(), status_code=response.status_code)

@app.get("/developer/integration/productCategoryList/{developer_id}",dependencies=[Depends(JWTBearer())], tags=['Products'], description="get product category list")
async def get_product_category_list(developer_id :str | None = Path(min_length= 5,max_length=16), token: str = Depends(JWTBearer())):
    token_valid = validate_token_developer_id(developer_id,token)
    if token_valid == None:
        json_compatible_item_data = jsonable_encoder({"status":False, "message": "err_forbidden", "data":[]})
        return JSONResponse(content=json_compatible_item_data,status_code=403)
    tent_data = find_tent_master_by_developer_id(developer_id)
    allowed_api_list = validate_api(token_valid.tent_id, '/developer/integration/productCategoryList')
    if not allowed_api_list:
        json_compatible_item_data = jsonable_encoder({"status":False, "message": "err_forbidden", "data":[]})
        return JSONResponse(content=json_compatible_item_data,status_code=403)
    headers = {
        'Internal': 'LYFnGO',
        'Content-Type': 'application/json'
    }
    url = lyfngo_services_url+f"/products/get/categoryListByTentUuid/{tent_data.tbl_tent_master.mast_tent_uuid}"
    response = requests.request("GET", url, headers=headers, data="")
    return JSONResponse(content=response.json(), status_code=response.status_code)

@app.get("/developer/integration/inventoryItemsList/{developer_id}",dependencies=[Depends(JWTBearer())], tags=['Products'], description="get inventry items list")
async def inventory_items_list(developer_id :str | None = Path(min_length= 5,max_length=16), token: str = Depends(JWTBearer())):
    token_valid = validate_token_developer_id(developer_id,token)
    if token_valid == None:
        json_compatible_item_data = jsonable_encoder({"status":False, "message": "err_forbidden", "data":[]})
        return JSONResponse(content=json_compatible_item_data,status_code=403)
    allowed_api_list = validate_api(token_valid.tent_id, '/developer/integration/inventoryItemsList')
    if not allowed_api_list:
        json_compatible_item_data = jsonable_encoder({"status":False, "message": "err_forbidden", "data":[]})
        return JSONResponse(content=json_compatible_item_data,status_code=403)
    headers = {
        'Internal': 'LYFnGO',
        'Content-Type': 'application/json'
    }
    tent_data = find_tent_master_by_developer_id(developer_id)
    url = lyfngo_services_url+f"/products/findAll/inventory-items/for/tentMaster/{tent_data.tbl_tent_master.mast_tent_uuid}"
    response = requests.request("GET", url, headers=headers, data="")
    return JSONResponse(content=response.json(), status_code=response.status_code)

@app.get("/developer/integration/customerList/{developer_id}",dependencies=[Depends(JWTBearer())], tags=['Appointments'], description="get customers list")
async def get_customers_list(developer_id :str | None = Path(min_length= 5,max_length=16), token: str = Depends(JWTBearer())):
    token_valid = validate_token_developer_id(developer_id,token)
    if token_valid == None:
        json_compatible_item_data = jsonable_encoder({"status":False, "message": "err_forbidden", "data":[]})
        return JSONResponse(content=json_compatible_item_data,status_code=403)
    allowed_api_list = validate_api(token_valid.tent_id, '/developer/integration/customerList')
    if not allowed_api_list:
        json_compatible_item_data = jsonable_encoder({"status":False, "message": "err_forbidden", "data":[]})
        return JSONResponse(content=json_compatible_item_data,status_code=403)
    customer_list = get_customer_list_by_tent_id(token_valid.tent_id, None)
    if customer_list == None:
        json_compatible_item_data = jsonable_encoder({"status":True, "message": "suc_customerList", "data":[]})
        return JSONResponse(content=json_compatible_item_data,status_code=200)
    json_compatible_item_data = jsonable_encoder({"status":True, "message": "suc_customerList", "data":customer_list})
    return JSONResponse(content=json_compatible_item_data,status_code=200)

@app.get("/developer/integration/usersList/{developer_id}",dependencies=[Depends(JWTBearer())], tags=['Appointments'], description="get practice users list")
async def get_users_list(developer_id :str | None = Path(min_length= 5,max_length=16), token: str = Depends(JWTBearer())):
    token_valid = validate_token_developer_id(developer_id,token)
    if token_valid == None:
        json_compatible_item_data = jsonable_encoder({"status":False, "message": "err_forbidden", "data":[]})
        return JSONResponse(content=json_compatible_item_data,status_code=403)
    allowed_api_list = validate_api(token_valid.tent_id, '/developer/integration/usersList')
    if not allowed_api_list:
        json_compatible_item_data = jsonable_encoder({"status":False, "message": "err_forbidden", "data":[]})
        return JSONResponse(content=json_compatible_item_data,status_code=403)
    headers = {
        'Internal': 'LYFnGO',
        'Content-Type': 'application/json'
    }
    tent_data = find_tent_master_by_developer_id(developer_id)
    url = lyfngo_services_url+f"communication/dashboardTopPerformer/{tent_data.tbl_tent_master.mast_tent_uuid}"
    response = requests.request("GET", url, headers=headers, data="")
    return JSONResponse(content=response.json(), status_code=response.status_code)

@app.post("/developer/integration/woocommerce/webhooks/orders/created/{developer_id}/lyfngoAccountId/{lyfngo_account_id}",tags=['Woocommerce'], description="Woocommerce orders webhooks")
async def orders_add_webhooks(input_data:Request,lyfngo_account_id:str, developer_id :str | None = Path(min_length= 5,max_length=16)):
    try:
        json_data = await input_data.json()
        tent_data = find_tent_master_by_developer_id(developer_id)
        if tent_data == None or tent_data.tbl_tent_master.mast_tent_uuid != lyfngo_account_id:
            raise HTTPException(status_code=404, detail="err_eastablishmentDetails")
        
        allowed_api_list = validate_api(tent_data.tbl_tent_master.tent_id, '/developer/integration/woocommerce/webhooks/orders')
        if not allowed_api_list:
            raise HTTPException(status_code=403, detail="err_forbidden")
        if json_data['status'] == 'processing':
            if json_data.get('customer_id') == None:
                return
            cust_data = get_customer_by_wooc_id(json_data.get('customer_id'))
            if cust_data.get('cust_uuid') == None:
                return 
            for i in json_data['line_items']:
                if i.get('product_id') == None:
                    return 
                product_data = get_product_by_wooc_id(i.get('product_id'))
                if product_data.get('tent_product_uuid') == None:
                    return 
                url = f"{lyfngo_services_url}products/consolidated/wooCommerce"
                payload = json.dumps({
                    "mastTentUuid": tent_data.tbl_tent_master.mast_tent_uuid,
                    "custUuid": cust_data['cust_uuid'],
                    "productUuid": product_data['tent_product_uuid'],
                    "price": int(i.get('total')),
                    "unit": i.get('quantity'),
                    "isMailsend": "false",
                    "modeType":"Cash",
                    "wooCommerceId":json_data.get('id')
                })


                headers = {
                    'Internal': 'LYFnGO',
                    'Content-Type': 'application/json'
                }
                response = requests.request("POST", url, headers=headers, data=payload)
        return JSONResponse(content={
            "status":True,
            "message":"suc_ordersCreated",
            "data":json_data
        }, status_code=200)
    except ValueError:
        return True
@app.post("/developer/integration/woocommerce/webhooks/orders/updated/{developer_id}/lyfngoAccountId/{lyfngo_account_id}",tags=['Woocommerce'], description="Woocommerce orders webhooks")
async def orders_update_webhooks(input_data:Request,lyfngo_account_id:str, developer_id :str | None = Path(min_length= 5,max_length=16)):
    try:
        json_data = await input_data.json()
        tent_data = find_tent_master_by_developer_id(developer_id)
        if tent_data == None or tent_data.tbl_tent_master.mast_tent_uuid != lyfngo_account_id:
            raise HTTPException(status_code=404, detail="err_eastablishmentDetails")
        
        allowed_api_list = validate_api(tent_data.tbl_tent_master.tent_id, '/developer/integration/woocommerce/webhooks/orders')
        if not allowed_api_list:
            raise HTTPException(status_code=403, detail="err_forbidden")
        
        return JSONResponse(content={
            "status":True,
            "message":"suc_ordersCreated",
            "data":json_data
        }, status_code=200)
    except ValueError:
        return True
@app.post("/developer/integration/woocommerce/webhooks/orders/deleted/{developer_id}/lyfngoAccountId/{lyfngo_account_id}",tags=['Woocommerce'], description="Woocommerce orders webhooks",status_code = 200,deprecated=False)
async def orders_delete_webhooks(input_data:Request,lyfngo_account_id:str, developer_id :str | None = Path(min_length= 5,max_length=16)):
    try:
        json_data = await input_data.json()
        tent_data = find_tent_master_by_developer_id(developer_id)
        if tent_data == None or tent_data.tbl_tent_master.mast_tent_uuid != lyfngo_account_id:
            raise HTTPException(status_code=404, detail="err_eastablishmentDetails")
        
        allowed_api_list = validate_api(tent_data.tbl_tent_master.tent_id, '/developer/integration/woocommerce/webhooks/orders')
        if not allowed_api_list:
            raise HTTPException(status_code=403, detail="err_forbidden")
        
        return JSONResponse(content={
            "status":True,
            "message":"suc_ordersCreated",
            "data":json_data
        }, status_code=200)
    except ValueError:
        return True
@app.post("/developer/integration/woocommerce/webhooks/product/created/{developer_id}/lyfngoAccountId/{lyfngo_account_id}",tags=['Woocommerce'], description="Woocommerce products webhooks",status_code = 200,deprecated=False)
async def products_add_webhooks(input_data:Request,lyfngo_account_id:str, developer_id :str | None = Path(min_length= 5,max_length=16)):
    try:
        json_data = await input_data.json()
        tent_data = find_tent_master_by_developer_id(developer_id)
        if tent_data == None or tent_data.tbl_tent_master.mast_tent_uuid != lyfngo_account_id:
            raise HTTPException(status_code=404, detail="err_eastablishmentDetails")
        
        allowed_api_list = validate_api(tent_data.tbl_tent_master.tent_id, '/developer/integration/woocommerce/webhooks/orders')
        if not allowed_api_list:
            raise HTTPException(status_code=403, detail="err_forbidden")
        
        return JSONResponse(content={
            "status":True,
            "message":"suc_ordersCreated",
            "data":json_data
        }, status_code=200)
    except ValueError:
        return True
@app.post("/developer/integration/woocommerce/webhooks/product/updated/{developer_id}/lyfngoAccountId/{lyfngo_account_id}",tags=['Woocommerce'], description="Woocommerce products webhooks",status_code = 200,deprecated=False)
async def products_update_webhooks(input_data:Request,lyfngo_account_id:str, developer_id :str | None = Path(min_length= 5,max_length=16)):
    try:
        json_data = await input_data.json()
        tent_data = find_tent_master_by_developer_id(developer_id)
        if tent_data == None or tent_data.tbl_tent_master.mast_tent_uuid != lyfngo_account_id:
            raise HTTPException(status_code=404, detail="err_eastablishmentDetails")
        
        allowed_api_list = validate_api(tent_data.tbl_tent_master.tent_id, '/developer/integration/woocommerce/webhooks/orders')
        if not allowed_api_list:
            raise HTTPException(status_code=403, detail="err_forbidden")
        
        return JSONResponse(content={
            "status":True,
            "message":"suc_ordersCreated",
            "data":json_data
        }, status_code=200)
    except ValueError:
        return True
@app.post("/developer/integration/woocommerce/webhooks/product/deleted/{developer_id}/lyfngoAccountId/{lyfngo_account_id}",tags=['Woocommerce'], description="Woocommerce products webhooks",status_code = 200,deprecated=False)
async def products_delete_webhooks(input_data:Request,lyfngo_account_id:str, developer_id :str | None = Path(min_length= 5,max_length=16)):
    try:
        json_data = await input_data.json()
        tent_data = find_tent_master_by_developer_id(developer_id)
        if tent_data == None or tent_data.tbl_tent_master.mast_tent_uuid != lyfngo_account_id:
            raise HTTPException(status_code=404, detail="err_eastablishmentDetails")
        
        allowed_api_list = validate_api(tent_data.tbl_tent_master.tent_id, '/developer/integration/woocommerce/webhooks/orders')
        if not allowed_api_list:
            raise HTTPException(status_code=403, detail="err_forbidden")
        
        #  woocommerce product delete from SIT to UAT
        url = f"{lyfngo_services_url}products/delete/productsByUuid/{json_data.get('id')}"
        payload = ""
        headers = {
        'Internal': 'LYFnGO'
        }
        response = requests.request("DELETE", url, headers=headers, data=payload)
        return JSONResponse(content={
            "status":True,
            "message":"suc_ordersCreated",
            "data":json_data
        }, status_code=200)
    except ValueError:
        return True


@app.post("/developer/integration/woocommerce/webhooks/customer_creation/{developer_id}/lyfngoAccountId/{lyfngo_account_id}",tags=['Woocommerce'], description="Woocommerce customer webhooks")
async def customer_webhooks(input_data:Request,lyfngo_account_id:str,developer_id :str | None = Path(min_length= 5,max_length=16)):
    try:
        json_data = await input_data.json()
        tent_data = find_tent_master_by_developer_id(developer_id)
        if tent_data == None or tent_data.tbl_tent_master.mast_tent_uuid != lyfngo_account_id:
            raise HTTPException(status_code=404, detail="err_eastablishmentDetails")
        
        allowed_api_list = validate_api(tent_data.tbl_tent_master.tent_id, '/developer/integration/woocommerce/webhooks/customer_creation')
        if not allowed_api_list:
            raise HTTPException(status_code=403, detail="err_forbidden")
        
        tent_integeration_data = get_tenant_integeration_config(tent_id = tent_data.tbl_tent_master.tent_id, integration_category = 'woocommerce',integration_name = 'woocommerce')
        if tent_integeration_data == None:
            raise HTTPException(status_code=404, detail="err_IntegerationValues")
        tent_integeration_json = json.loads(tent_integeration_data)

        # Set your API credentials
        consumer_key = tent_integeration_json['WOO_COMMERCE_CONSUMER_KEY']
        consumer_secret = tent_integeration_json['WOO_COMMERCE_SECRECT_KEY']

        # set woocommerce url & version
        woocommerce_url = tent_integeration_json['WOO_COMMERCE_BASEURL']
        woocomerce_version = tent_integeration_json['WOO_COMMERCE_API_VERSION']

        # Set up the API client
        # wcapi = API(
        #     url=woocommerce_url,
        #     consumer_key=consumer_key,
        #     consumer_secret=consumer_secret,
        #     version=woocomerce_version,
        #     timeout=10
        # )

        # customer = wcapi.get(f"customers/{customer_id}", params={"force": True}).json()
        customer = json_data

        if customer.get('meta_data'):
            meta_data_dial_code = meta_data_mobile_number = ''
            for i in customer['meta_data']:
                if i['key'] == 'user_registration_mobile_no':
                    meta_data_mobile_number = i['value']
                if i['key'] == 'user_registration_country_code':
                    meta_data_dial_code = i['value']
            lyf_cust_check = get_customer_by_attrs(tent_id=tent_data.tbl_tent_master.tent_id,mobile_number=meta_data_mobile_number, email=customer['email'])      
            if lyf_cust_check != None:
                return True
            patient_creation({
                "mast_tent_uuid":tent_data.tbl_tent_master.mast_tent_uuid,
                "customer_name":customer["first_name"],
                "email":customer['email'],
                "dail_code":meta_data_dial_code,
                "mobile_number":meta_data_mobile_number,
                "woocommerce_id":json_data.get('id')
            })
            return JSONResponse(content={
                "status":True,
                "message":"suc_customerCreated",
                "data":[]
            }, status_code=200)
        else:
            raise HTTPException(status_code=404, detail='Ivalid Customer')
    except ValueError:
        # raise HTTPException(status_code=400, detail="Invalid JSON data")
        return True

@app.post("/developer/integration/customer_creation/{developer_id}",dependencies=[Depends(JWTBearer())], tags=['Appointments'], description="customer creation")
async def customer_creation(input_data:add_customer,developer_id :str | None = Path(min_length= 5,max_length=16),token: str = Depends(JWTBearer())):
    try:
        # return input_data
        token_valid = validate_token_developer_id(developer_id,token)
        if token_valid == None:
            raise HTTPException(status_code=403, detail="err_forbidden")
        allowed_api_list = validate_api(token_valid.tent_id, '/developer/integration/woocommerce/webhooks/customer_creation')
        if not allowed_api_list:
            raise HTTPException(status_code=403, detail="err_forbidden")
        headers = {
        'Internal': 'LYFnGO'
        }
        tent_data = find_tent_master_by_developer_id(developer_id)
        url = lyfngo_services_url+f"users/customer/getPatientid/{tent_data.tbl_tent_master.mast_tent_uuid}"
        response = requests.request("GET", url, headers=headers, data="")

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail='err_customer_creation')
        iv = response.headers.get('key')
        response_text = response.text

        aesObj = AESCipher(aes_secret_key.encode())
        dec_value = aesObj.decrypt(response_text,iv.encode())
        patient_id_json = json.loads(dec_value)
        client_dict = {
            "custName": input_data.customer_name,
            "custCustomId": patient_id_json['data'],
            "custEmail": input_data.customer_email,
            "custCountryCode": f"+{input_data.dial_code}",
            "custMobileNo": str(input_data.mobile_number),
            "custMobileNotification": False,
            "custEmailNotification": False,
            "isAddress": False
        }
        encrypted_json_text =  json.dumps(client_dict)
        value = aesObj.encrypt(encrypted_json_text.encode(),iv.encode())
        payload = {
            "data":value.decode()
        }
        headers = {
            'Internal': 'LYFnGO',
            'Content-Type': 'application/json',
            "Key":iv
        }
        url = lyfngo_services_url+f"users/customer/saveCustomerMaster/{tent_data.tbl_tent_master.mast_tent_uuid}"
        response = requests.request(
            "POST", url, headers=headers, data=json.dumps(payload))
        dec_value = aesObj.decrypt(response.text,iv.encode())


        return JSONResponse(content={
            "data":True
        }, status_code=response.status_code)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid JSON data")



class rnr_whatsapp_notification(SQLModel):
    name:str
    mobile_number: int
    # country_code: Union[str, int]
    country_code: int
    isp: str
    template_name:str
    template_params:dict
    class Config:
        schema_extra = {
            "example": {
                "name":"name",
                "mobile_number":1234567890,
                "country_code":91,
                "isp":"clinic",
                "template_name":"lyfngo_active_anr",
                "template_params":{"1":"name", "2":"date"}
            }
        }
        
@app.post("/developer/integration/crmWhatsAppNotification/activeRnr/{developer_id}",dependencies=[Depends(JWTBearer())], tags=['CRM'], description="CRM whatsapp Notification")
async def fn_rnr_nofification(input_data:rnr_whatsapp_notification,developer_id :str | None = Path(min_length= 5,max_length=16),token: str = Depends(JWTBearer())):
    try:
        input_dict = input_data.__dict__
        # if str(input_dict["country_code"])[0] == "+":
        #     changed_country_code = str(input_dict["country_code"])[1:]
        #     input_dict["country_code"] = changed_country_code
          
        token_valid = validate_token_developer_id(developer_id,token)
        if token_valid == None:
            raise HTTPException(status_code=403, detail="err_forbidden")
        allowed_api_list = validate_api(token_valid.tent_id, '/developer/integration/crmWhatsAppNotification/activeRnr')
        if not allowed_api_list:
            raise HTTPException(status_code=403, detail="err_forbidden")
        tent_data = find_tent_master_by_developer_id(developer_id)

        # access_token = get_old_propery_integeration(tent_id = tent_data.tbl_tent_master.tent_id,integration_category='Whatsapp',tent_property_config_name='ACCESS_TOKEN')
        # phone_number_id = get_old_propery_integeration(tent_id = tent_data.tbl_tent_master.tent_id,integration_category='Whatsapp',tent_property_config_name='PHONE_NUMBER_ID')
        # bussiness_id = get_old_propery_integeration(tent_id = tent_data.tbl_tent_master.tent_id,integration_category='Whatsapp',tent_property_config_name='WHATSAPP_BUSINESS_ACCOUNT_ID')
        
        # tent_integeration_data = get_tenant_integeration_config(tent_id = tent_data.tbl_tent_master.tent_id, integration_category = 'messaging',integration_name = 'whatsapp')
        # if access_token == None or phone_number_id == None:
        #     raise HTTPException(status_code=404, detail="err_IntegerationValues")

        # ACCESS_TOKEN = access_token
        # PHONE_NUMBER_ID = phone_number_id

        ACCESS_TOKEN = wa_lyfngo_token
        PHONE_NUMBER_ID = wa_lyfngo_phone_id
        BUSINESS_ACCOUNT_ID = wa_lyfngo_busienss_account_id

        WA_VERSION = 'v17.0'

        is_opt_out = await wa_opt_out_check(phone_number_id=str(PHONE_NUMBER_ID),customer_mobile_number=f"{input_dict['country_code']}{input_dict['mobile_number']}")
        if not is_opt_out:
            return JSONResponse(content={
                "data": True,
                "wa_status": "opt-outed",
                "message": "suc_crnNotified"
            }, status_code=200)


        whatsapp_template_formate = TemplatePatten(template_name=input_data.template_name, mobile_number=input_data.mobile_number, country_code=input_data.country_code,template_params=input_data.template_params)
        if bool(whatsapp_template_formate) == False:
            return JSONResponse(content={"data":False, "message":str(whatsapp_template_formate)}, status_code=400)
        wa_response = whatsapp_template_formate.send_message()    
        wa_response_json=wa_response["response"].json()
        wa_api_status_code=wa_response["response"].status_code
        
        contact = wa_response_json['contacts'][0].get('wa_id') if wa_response_json and wa_api_status_code == 200 else f"{input_dict['country_code']}{input_dict['mobile_number']}"
        wa_id = wa_response_json['messages'][0].get('id') if wa_response_json and wa_api_status_code == 200 else None
        templeted_log_insert(wa_id, f"{input_dict['country_code']}{input_dict['mobile_number']}", developer_id, cust_uuid=None, message=whatsapp_template_formate.actual_message_body, template_name=None, message_type="ZOHO")
        
        mongo_insert_data = {
            "number":contact,
            "message":whatsapp_template_formate.actual_message_body,
            "wa_id":wa_id,
            "wa_api_status_code":wa_api_status_code,
            "wa_request":wa_response["requests"],
            "wa_response":wa_response_json
        }
        await zoho_crm_history(mongo_insert_data)
        if wa_response["response"].status_code != 200:
            raise HTTPException(status_code=404, detail="err_wa_undelivered")
        wa_status = "Delivered" if wa_response["response"].status_code == 200 else 'Un Delivered'
        
        headers = {
            'Internal' : 'LYFnGO'
        }
        url = lyfngo_services_url+f"users/customer/getPatientid/{tent_data.tbl_tent_master.mast_tent_uuid}"
        response = requests.request("GET", url, headers=headers, data="")

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail='err_customer_creation')
        iv = response.headers.get('key')
        response_text = response.text
        aesObj = AESCipher(aes_secret_key.encode())
        dec_value = aesObj.decrypt(response_text,iv.encode())
        patient_id_json = json.loads(dec_value)
        client_dict = {
            "custName": input_dict['name'],
            "custCustomId": patient_id_json['data'],
            "custCountryCode": f"+{input_dict['country_code']}",
            "custMobileNo": str(input_dict['mobile_number']),
            "custMobileNotification": False,
            "custEmailNotification": False,
            "isAddress": False,
            "sourceFrom":'Lead',
            "leadStatus": 'Lead',
        }
        encrypted_json_text =  json.dumps(client_dict)
        value = aesObj.encrypt(encrypted_json_text.encode(),iv.encode())
        payload = {
            "data":value.decode()
        }

        customer_exists = get_customer_list_by_tent_id(tent_data.tbl_tent_master.tent_id, f"{input_dict['mobile_number']}")
        cust_uuid = None
        if len(customer_exists) > 0:
            cust_uuid = customer_exists[0]['cust_id']
        else:
            headers = {
                'Internal': 'LYFnGO',
                'Content-Type': 'application/json',
                "Key":iv
            }
            url = lyfngo_services_url+f"users/customer/saveCustomerMaster/{tent_data.tbl_tent_master.mast_tent_uuid}"
            customer_response = requests.request(
                "POST", url, headers=headers, data=json.dumps(payload))
            if customer_response.status_code == 200:
                iv = customer_response.headers.get('key')
                customer_response_text = customer_response.text
                aesObj = AESCipher(aes_secret_key.encode())
                dec_value = aesObj.decrypt(customer_response_text, iv.encode())
                customer_response_dict = json.loads(dec_value)
                cust_uuid = customer_response_dict['data']['custUuid']
        if cust_uuid != None:
            zoho_status_dict = {
                "mast_tent_uuid":tent_data.tbl_tent_master.mast_tent_uuid,
                "cust_uuid":cust_uuid,
                "content": whatsapp_template_formate.actual_message_body,
                "token":f"{ACCESS_TOKEN}",
                "phone_id":f"{PHONE_NUMBER_ID}",
                "wamid":wa_id,
                "mobile_number":f"{input_dict['country_code']}{input_dict['mobile_number']}"
            }
            headers = {
                'Internal': 'LYFnGO',
                'Content-Type': 'application/json'
            }
            zoho_status_url = lyfngo_services_url+f"communication/consult/zohotrigger"
            zoho_status_response = requests.request("POST", zoho_status_url, headers=headers, data=json.dumps(zoho_status_dict))

        return JSONResponse(content={
            "data": True,
            "wa_status": wa_status,
            "message": "suc_crnNotified"
        }, status_code=200)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid JSON data")

# @app.get("/developer/integration/fb_callback",tags=['CRM'], description="CRM whatsapp Notification")
# async def callback_get(input_data:Request):
#     print(input_data.__dict__)
#     print(input_data.query_params)

