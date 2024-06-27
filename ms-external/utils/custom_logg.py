import logging
from fastapi import Response, APIRouter, Request
from fastapi.routing import APIRoute
from typing import Callable
import os,sys





class MyLogger:
   

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)  # Set the base log level to DEBUG

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        if not self.logger.hasHandlers():
            # Create and add a DEBUG level handler
            debug_handler = logging.StreamHandler()
            debug_handler.setLevel(logging.DEBUG)
            debug_handler.setFormatter(formatter)
            self.logger.addHandler(debug_handler)

            # Create and add an INFO level handler
            info_handler = logging.StreamHandler()
            info_handler.setLevel(logging.INFO)
            info_handler.setFormatter(formatter)
            self.logger.addHandler(info_handler)

            # Create and add a WARNING level handler
            warning_handler = logging.StreamHandler()
            warning_handler.setLevel(logging.WARNING)
            warning_handler.setFormatter(formatter)
            self.logger.addHandler(warning_handler)

            

            # Configure Lambda environment-specific logging
            if os.environ.get("AWS_EXECUTION_ENV") == "AWS_Lambda_python3.11":
                lambda_handler = logging.StreamHandler()
                lambda_handler.setLevel(logging.INFO)  # Adjust log level as needed
                lambda_handler.setFormatter(formatter)
                self.logger.addHandler(lambda_handler)

    def log_debug(self, message):
        self.logger.debug(message)

    def log_info(self, message):
        self.logger.info(message)

    def log_warning(self, message):
        self.logger.warning(message)

    def log_error(self, message):
        self.logger.error(message)

    def log_critical(self, message):
        self.logger.critical(message)

    def log_exception(self, message=None, exc_info=True):
        if exc_info:
            self.logger.error(message, exc_info=sys.exc_info())
        else:
            self.logger.error(message)
    
 
 
my_logger = MyLogger()   

class log_stuff(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            my_logger.log_debug("************************fastapi request start*********************************")
            req = await request.body()
            my_logger.log_info(f"Request:{str(req)}")
            response: Response = await original_route_handler(request)
            my_logger.log_info(f"Response:{str(response.body)}")
            my_logger.log_debug("************************fastapi request end*********************************")
            return response

        return custom_route_handler
    
    
    
    

class CustomRouter(APIRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.route_class = log_stuff