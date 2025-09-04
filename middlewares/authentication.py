import logging
import jwt
import uuid

from django.conf import settings
from django.http import JsonResponse
from error_handling.custom_exception import CustomErrorWithCode
from students.enums import ServiceList

from students.models import ServiceKey


class AuthMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    @staticmethod
    def is_swagger_path(path):
        return path == '/swagger/'

    @staticmethod
    def is_synctera_request(request):
        return 'synctera-signature' in request.headers

    @staticmethod
    def is_persona_request(request):
        return 'persona-signature' in request.headers

    @staticmethod
    def get_jwt_token_from_request(request):
        auth_header_prefix = 'Bearer '
        auth_header = request.META.get('HTTP_AUTHORIZATION')

        if auth_header and auth_header.startswith(auth_header_prefix):
            return auth_header[len(auth_header_prefix):]
        else:
            return None

    @staticmethod
    def get_json_from_error(error):
        return {
            'error': {
                'message': error.message,
                'code': error.code
            }
        }

    def get_json_response_with_error(self, error, status_code, extra_data=None):
        response_data = self.get_json_from_error(error)
        if extra_data:
            response_data.update(extra_data)
        return JsonResponse(response_data, status=status_code)

    @staticmethod
    def get_jwt_raw_token_from_request(request):
        auth_header_prefix = 'Bearer '
        auth_header = request.META.get('HTTP_AUTHORIZATION')

        if auth_header and auth_header.startswith(auth_header_prefix):
            return auth_header[len(auth_header_prefix):]
        else:
            return None

    def __call__(self, request):
        request.request_id = str(uuid.uuid4())
        request.auth_token = self.get_jwt_raw_token_from_request(request)

        api_key = request.headers.get('x-api-key', None)
        service = ServiceKey.get_service_from_api_key(api_key)
        request.service = service

        if bool(settings.IS_SWAGGER_ENABLED) and self.is_swagger_path(request.path):
            return self.get_response(request)

        if request.service not in ServiceList.get_student_service_list():
            permission_error = CustomErrorWithCode(code=403, message='You are not permitted to access this API')
            return self.get_json_response_with_error(permission_error, 403)

        return self.get_response(request)
