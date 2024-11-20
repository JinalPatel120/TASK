
import logging
from django.db import connection
from django.utils.deprecation import MiddlewareMixin
import logging
import json
from django.utils.timezone import now
import os

# Get the logger for the application
logger = logging.getLogger('django')

class SqlLoggerMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """
        This method is called before the request is processed.
        It logs the message "Request Sent".
        """
        logger.info("Request Sent: %s %s", request.method, request.path)
    
    def process_response(self, request, response):
        """
        This method logs SQL queries executed during the request
        and the message "Request Completed".
        """
        
        sql_queries = connection.queries

        if sql_queries:
            logger.info("SQL Queries executed during this request:")
            for query in sql_queries:
                logger.info(f" <--- {query['sql']} ---> \n")
        else:
            logger.info("No SQL queries executed during this request.")
   
        logger.info("Request Completed: %s %s", request.method, request.path)
        
        return response


# import logging
# import json
# from django.utils.timezone import now

# class RequestResponseLoggingMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response
#         self.request_logger = logging.getLogger("request_logger")
#         self.response_logger = logging.getLogger("response_logger")

#     def __call__(self, request):
#         # Log the incoming request
#         self._log_request(request)

#         # Get the response from the next middleware or view
#         response = self.get_response(request)

#         # Log the outgoing response
#         self._log_response(request, response)

#         return response

#     # middleware.py

#     def _log_request(self, request):
#         # Only decode the body if it's not a file upload
#         if 'multipart/form-data' not in request.content_type:
#             try:
#                 body = request.body.decode('utf-8')
#             except UnicodeDecodeError:
#                 body = None
#         else:
#             body = None  # For file uploads, set body to None or handle differently

#         # Log the request with or without the body (depending on your needs)
#         self.logger.info(f"Request body: {body}")


#     def _log_response(self, request, response):
#         """
#         Logs the outgoing response.
#         """
#         body = "N/A"
#         if response.content:
#             body = response.content.decode('utf-8')

#         self.response_logger.info({
#             "method": request.method,
#             "path": request.get_full_path(),
#             "status_code": response.status_code,
#             "body": body,
#             "timestamp": now().isoformat(),
#         })
