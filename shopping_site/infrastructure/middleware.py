
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




# myapp/middleware/logging_middleware.py

# shopping_site/middleware/request_response_logging.py

import logging
import json
from django.utils.timezone import now

class RequestResponseLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_logger = logging.getLogger("request_logger")
        self.response_logger = logging.getLogger("response_logger")

    def __call__(self, request):
        # Log the incoming request
        self._log_request(request)

        # Get the response from the next middleware or view
        response = self.get_response(request)

        # Log the outgoing response
        self._log_response(request, response)

        return response

    def _log_request(self, request):
        """
        Logs the incoming request.
        """
        body = "N/A"
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = json.dumps(request.json())  # Django request body (assuming JSON)
            except:
                body = request.body.decode('utf-8')

        self.request_logger.info({
            "method": request.method,
            "path": request.get_full_path(),
            "headers": dict(request.headers),
            "body": body,
            "timestamp": now().isoformat(),
        })

    def _log_response(self, request, response):
        """
        Logs the outgoing response.
        """
        body = "N/A"
        if response.content:
            body = response.content.decode('utf-8')

        self.response_logger.info({
            "method": request.method,
            "path": request.get_full_path(),
            "status_code": response.status_code,
            "body": body,
            "timestamp": now().isoformat(),
        })
