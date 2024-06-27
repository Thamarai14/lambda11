from fastapi import APIRouter, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from time import time
from pydantic import EmailStr
from sqlmodel import SQLModel, Field
from utils.custom_logg import CustomRouter
from auth.jwt_auth import encode_token, decode_token
# from auth.jwt_bearer import JWTBearer
# from pymongo import MongoClient
# from pymongo.errors import ConnectionFailure
# from bson.objectid import ObjectId
# from bson.json_util import dumps
# from dotenv import load_dotenv
from models.common import check_password,developer_account_creation,find_tent_master_by_uuid,find_developer_account_by_tent_id,find_tent_master_by_developer_id
registration_router = CustomRouter()


class signup_schema(SQLModel):
    email: EmailStr = Field(default=None)
    password: str = Field(default=None)
    lyfngoAccountId: str = Field(default=None)

    class Config:
        schema_extra = {
            "example": {
                "email": "sample@email.com",
                "password": "XYZ",
                "lyfngoAccountId": "LYF_xyzzzzzzzz"
            }
        }


class login_schema(SQLModel):
    # email: EmailStr = Field(default=None)
    # password: str = Field(default=None)
    developerId: str
    lyfngoAccountId: str

    class Config:
        schema_extra = {
            "example": {
                # "email": "sample@email.com",
                "developerId": "XYZ",
                "lyfngoAccountId": "LYF_xyzzzzzzzz"

            }
        }


@registration_router.post("/developer/integration/signup", tags=["Authentication"], description="LYFnGO developer account signup API")
async def sign_up(input_data: signup_schema):
    payload = input_data.__dict__
    validate_user = check_password(tent_uuid = payload["lyfngoAccountId"],password = payload['password'],email = payload['email'])
    if not validate_user:
        json_compatible_item_data = jsonable_encoder({"status":False,"developerId":None,"message": "error_invalid_user","data":[],"lyfngoAccountId":payload['lyfngoAccountId']})
        return JSONResponse(content=json_compatible_item_data,status_code=404)
    tent_data = find_tent_master_by_uuid(payload['lyfngoAccountId'])
    if tent_data == None:
        json_compatible_item_data = jsonable_encoder({"status":False,"developerId":None,"message": "err_tentData","data":[],"lyfngoAccountId":payload['lyfngoAccountId']})
        return JSONResponse(content=json_compatible_item_data,status_code=404)
    
    dev_account_data = find_developer_account_by_tent_id(tent_data.tent_id)
    if dev_account_data != None:
        json_compatible_item_data = jsonable_encoder({"status":False,"message": "err_registration","data":[],"lyfngoAccountId":payload['lyfngoAccountId']})
        return JSONResponse(content=json_compatible_item_data,status_code=404)
    return_data = developer_account_creation({
        "tent_id":tent_data.tent_id,
        "email":payload['email']
    })

    if return_data != None:
        json_compatible_item_data = jsonable_encoder({"status":True,"developerId":return_data.developer_id,"message": "suc_registered_successfully","lyfngoAccountId":payload['lyfngoAccountId'],"data":{"access_token":return_data.lyfngo_permanent_token}})
        return JSONResponse(content=json_compatible_item_data,status_code=200)
    else:
        json_compatible_item_data = jsonable_encoder({"status":True,"developerId":None,"message": "suc_registered_successfully","data":None,"lyfngoAccountId":payload['lyfngoAccountId']})
        return JSONResponse(content=json_compatible_item_data,status_code=404)

@registration_router.post("/developer/integration/getToken", tags=["Authentication"], description="LYFnGO developer account sign In API")
async def get_lyfngo_Token(input_data: login_schema):
    try:

        payload = input_data.__dict__
        tent_data = find_tent_master_by_developer_id(payload['developerId'])
        if tent_data == None or tent_data.tbl_tent_master.mast_tent_uuid != payload['lyfngoAccountId']:
            raise HTTPException(status_code=404, detail='err_userNotFound')
        # return tent_data.tbl_tent_master.mast_tent_uuid
        # validate_user = check_password(tent_uuid = payload["lyfngoAccountId"],password = payload['password'],email = payload['email'])
        # if not validate_user:
        #     json_compatible_item_data = jsonable_encoder({"status":False,"developerId":None,"message": "err_invalid_user","data":None})
        #     return JSONResponse(content=json_compatible_item_data,status_code=404)
        # tent_data = find_tent_master_by_uuid(payload['lyfngoAccountId'])
        # if tent_data == None:
        #     json_compatible_item_data = jsonable_encoder({"status":False,"developerId":None,"message": "err_tentData","data":None})
        #     return JSONResponse(content=json_compatible_item_data,status_code=404)
        dev_account_data = find_developer_account_by_tent_id(tent_data.tbl_tent_master.tent_id)
        if dev_account_data != None:
            json_compatible_item_data = jsonable_encoder({"status":True,"developerId":dev_account_data.developer_id,"message": "suc_LYFnGO_token","data":{"access_token":dev_account_data.lyfngo_permanent_token}})
            return JSONResponse(content=json_compatible_item_data,status_code=200)
        json_compatible_item_data = jsonable_encoder({"status":False,"developerId":None,"message": "err_notFound","data":None})
        return JSONResponse(content=json_compatible_item_data,status_code=404)
    except ValueError:
        raise HTTPException(status_code=404, detail="err_userNotFound")



