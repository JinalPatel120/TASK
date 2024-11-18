
import logging
from django.db import connection
from django.utils.deprecation import MiddlewareMixin

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




# import jwt
# from django.conf import settings
# from django.http import JsonResponse
# from django.utils.deprecation import MiddlewareMixin
# from shopping_site.infrastructure.logger.models import logger

# class TokenAuthenticationMiddleware(MiddlewareMixin):
#     def process_request(self, request):
#         token = request.headers.get('Authorization')  # Get the token from the Authorization header

#         if token is None:
#             return JsonResponse({"error": "Authentication token is missing."}, status=401)

#         try:
#             # Decode the token to get user information
#             decoded_payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
#             request.user_id = decoded_payload['user_id']  # Store user ID in request object
#         except jwt.ExpiredSignatureError:
#             return JsonResponse({"error": "Token has expired."}, status=401)
#         except jwt.InvalidTokenError:
#             return JsonResponse({"error": "Invalid token."}, status=401)
