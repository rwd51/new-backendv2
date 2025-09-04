from django.http import JsonResponse
from rest_framework import status

from error_handling.custom_exception import CustomValidationError


def get_json_from_error(error):
    return {
        'error': {
            'message': error.message,
            'code': error.code
        }
    }


def get_json_from_validation_error(ex):
    error_message = str(ex.get_full_details()[0].get('message'))
    error_code = ex.get_codes()[0]
    return {
        'error': {
            'message': error_message,
            'code': error_code
        }
    }


def get_json_response_with_error(error, status_code, extra_data=None):
    response_data = get_json_from_error(error)
    if extra_data:
        response_data.update(extra_data)
    return JsonResponse(response_data, status=status_code)


def get_json_validation_error_response(ex: CustomValidationError):
    response_data = get_json_from_validation_error(ex)
    return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)
