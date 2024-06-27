import logging, os
import sys    
import requests
import textwrap
import logging.handlers
from pymongo import MongoClient
from datetime import datetime, timezone
from dotenv import load_dotenv
from pymongo.errors import ConnectionFailure
from fastapi.exceptions import HTTPException
root = logging.getLogger('httplogger')




load_dotenv()

mongo_db_url = os.getenv("MONGO_DB_URL")
try:
    cluster = MongoClient(mongo_db_url)
except ConnectionFailure:
    raise HTTPException(status_code=403, detail="err_mongo_connection")

db_name = cluster["whatsappbot"]
message_log_coll = db_name["meta_message_logs"]


def logRoundtrip(response, *args, **kwargs):
    extra = {'req': response.request, 'res': response}
    root.debug('HTTP roundtrip', extra=extra)
    # root.debug(extra)
    

class HttpFormatter(logging.Formatter):

    def _formatHeaders(self, d):
        return '\n'.join(f'{k}: {v}' for k, v in d.items())

    def formatMessage(self, record):
        result = super().formatMessage(record)
        if record.name == 'httplogger':
            result += textwrap.dedent('''
                ---------------- request ----------------
                {req.method} {req.url}
                {reqhdrs}

                {req.body}
                ---------------- response ----------------
                {res.status_code} {res.reason} {res.url}
                {reshdrs}

                {res.text}
            ''').format(
                req=record.req,
                res=record.res,
                reqhdrs=self._formatHeaders(record.req.headers),
                reshdrs=self._formatHeaders(record.res.headers),
            )
        return result

formatter = HttpFormatter('{asctime} {levelname} {name} {message}', style='{')
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
root.addHandler(handler)
root.setLevel(logging.DEBUG)

def request_session():
    session = requests.Session()
    session.hooks['response'].append(logRoundtrip)
    return session



def templeted_log_insert(wamid, recipent_no, devloper_id, cust_uuid:str=None, message_type = "zoho_crm", template_name:str=None, message:str=None, mainId=None):
    try:
        main_dict = {
            "meta_type": "zoho_crm",
            "meta_category": "utility",
            "lyfngo_type": message_type,
            "wa_id": wamid,
            "tent_id":devloper_id,
            "messages": message,
            "recipient_id": recipent_no,
            "is_read": None,
            "is_sent": None,
            "is_delivered": None,
            "is_approved": None,
            "is_rejected": None,
            "is_pending":None,
            "is_error": None,
            "created_on":str(datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")),
            "template_name":template_name,
            "cust_uuid":None,
            "mainId":None,
            "is_initiated": {
                "status": True,
                "created_on": None
            },
            "wa_status":"sent",
            "wa_created_on":str(datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
            }
        message_log_coll.insert_one(main_dict)
    except Exception:
      pass