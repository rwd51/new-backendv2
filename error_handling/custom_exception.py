from rest_framework import serializers


class CustomErrorWithCode(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message


class CeleryException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return 'Celery task error: ' + self.message


class CustomValidationError(serializers.ValidationError):
    def __init__(self, code, message):
        super().__init__(detail=message, code=code)
