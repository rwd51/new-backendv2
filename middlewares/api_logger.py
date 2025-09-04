# import re
# import socket
# import time
# import json
# from collections.abc import Mapping
# from datetime import datetime
# from json import JSONDecodeError
#
# from django.http import JsonResponse
# from django.utils import timezone
# from rest_framework import status
#
# from common.helpers import get_user_from_request_before_authentication
# from core.models import PriyoMoneyUser
# from pay_admin.models import PayAdmin
# from service.api_log_service import APILogService
# from core.enums import ServiceList, ActionStatus
# from webhook.mappings import synctera_webhook_entity_to_model_mapper, synctera_webhook_entity_to_event_resource_id_field_mapper
#
# api_logger = APILogService()
#
#
# class LoggingMiddleware:
#     """Request Logging Middleware."""
#
#     def __init__(self, get_response):
#         self.get_response = get_response
#
#     def __call__(self, request):
#         # Code to be executed for each request before
#         # the view (and later middlewares) are called.
#
#         request.start_time = time.time()
#         body = request.body
#         response = self.get_response(request)
#
#         # Code to be executed for each request/response after
#         # the view is called.
#
#         if request.path == '/swagger/':
#             return response
#
#         api_request_log = self.generate_log_from_request(request, body)
#         api_response_log = self.generate_log_from_response(request, response)
#
#         api_logger.log_api_call({**api_request_log, **api_response_log})
#
#         # todo: add activity
#         if self.should_generate_activity_log(request):
#             pass
#
#         return response
#
#     @staticmethod
#     def should_generate_activity_log(request):
#         return request.service == ServiceList.CLIENT.value and request.user
#
#     @staticmethod
#     def process_synctera_requests(req_body):
#         event_resource = req_body.get("event_resource", None)
#         event_resource_changed_fields = req_body.get("event_resource_changed_fields", None)
#         req_body["event_resource"] = json.loads(event_resource) if event_resource else None
#         req_body["event_resource_changed_fields"] = json.loads(event_resource_changed_fields) \
#             if event_resource_changed_fields else None
#         return req_body
#
#     def get_response_status(self, request, response):
#         try:
#             response_data = json.loads(response.content)
#         except JSONDecodeError:
#             response_data = {}
#
#         if hasattr(response, 'status_code'):
#             if (request.service == ServiceList.SYNCTERA.value and
#                     isinstance(response_data, Mapping) and response_data.get("skipped", False)):
#                 return ActionStatus.SKIPPED.value
#
#             return ActionStatus.SUCCESS.value if status.is_success(response.status_code) else ActionStatus.FAILED.value
#         return ActionStatus.UNKNOWN.value
#
#     def generate_log_from_response(self, request, response):
#         api_log = {}
#         if hasattr(response, 'status_code'):
#             api_log["response_code"] = response.status_code
#             api_log['response_status'] = self.get_response_status(request, response)
#
#         api_log['response_data'] = self.generate_json_response_data(response)
#         return api_log
#
#     @staticmethod
#     def generate_json_response_data(response):
#         if 'application/json' in response.get('content-type', '') and response["content-type"] == "application/json":
#             return json.loads(response.content.decode("utf-8"))
#         return {}
#
#     @staticmethod
#     def get_related_user_from_request(request, request_data):
#         if request.service == ServiceList.STUDENT.value:
#             user = request.user if hasattr(request, 'user') else get_user_from_request_before_authentication(request)
#             return user if isinstance(user, PriyoMoneyUser) else None
#
#         return None
#
#     @staticmethod
#     def get_related_admin_from_request(request):
#         if request.service == ServiceList.ADMIN.value:
#             admin_user =  request.user if hasattr(request, 'user') else None
#             if admin_user and isinstance(admin_user, PayAdmin):
#                 return admin_user
#
#         return None
#
#     def generate_log_from_request(self, request, request_body):
#         request_data = self.generate_json_request_body(request, request_body)
#         user = self.get_related_user_from_request(request, request_data)
#         admin = self.get_related_admin_from_request(request)
#         webhook_type = self.get_webhook_type_from_request(request, request_data)
#         api_log = {
#             "request_id": str(request.request_id),
#             "request_method": request.method,
#             "request_data": request_data,
#             "request_path": request.get_full_path(),
#             "request_header": self.generate_json_request_header(request),
#
#             "server_hostname": socket.gethostname(),
#             "remote_address": api_logger.get_client_ip(request),
#             "http_user_agent": request.META.get('HTTP_USER_AGENT'),
#
#             "user": user.pk if user else None,
#             "admin": admin.pk if admin else None,
#             "service": request.service,
#             "sub_service": request.sub_service,
#             "run_time": time.time() - request.start_time,
#             "created_at": timezone.now(),
#             "webhook_type": webhook_type,
#         }
#         return api_log
#
#     def generate_json_request_body(self, request, request_body):
#         json_data = {}
#         if request.META and 'application/json' in request.META.get('CONTENT_TYPE', '') and request_body:
#
#             try:
#                 json_data = json.loads(request_body.decode("utf-8"))
#             except Exception:
#                 # not handling if body is malformed
#                 pass
#
#         if request.service == ServiceList.SYNCTERA.value:
#             json_data = self.process_synctera_requests(json_data)
#
#         return json_data
#
#     @staticmethod
#     def generate_json_request_header(request):
#         regex = re.compile('^HTTP_')
#         header_dict = dict((regex.sub('', header), value) for (header, value)
#                            in request.META.items() if header.startswith('HTTP_'))
#         return header_dict
