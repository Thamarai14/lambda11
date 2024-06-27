# from elasticapm.contrib.starlette import make_apm_client, ElasticAPM
# from dotenv import load_dotenv
# import os, logging
# load_dotenv()

# apm_server_url = os.getenv("APM_SERVER_URL")
# apm_token= os.getenv("APM_TOKEN")
# apm_environment = os.getenv("APM_ENVIRONMENT")
# logging.getLogger('elasticapm').setLevel(logging.WARNING)



# apm = make_apm_client({
#   'SERVICE_NAME': 'ms-extranl-api',
#   'SECRET_TOKEN': apm_token,
#   'SERVER_URL': apm_server_url,
#   'ENVIRONMENT': apm_environment,
#   "VERIFY_SERVER_CERT":False,
#   "CAPTURE_EXCEPTIONS": True,
#   "CAPTURE_HEADERS": True,
#   "TRANSACTION_MAX_SPANS": 250,
#   "STACK_TRACE_LIMIT": 250,
#   "TRANSACTION_SAMPLE_RATE": 0.5,
#   "CAPTURE_BODY":"all"
  
  
# })