import logging

from bank_admin.permissions import verify_supabase_jwt
from rest_framework import permissions
from django.conf import settings
from students.enums import ServiceList
from students.models import StudentUser, CustomUser
from bank_admin.models import BankAdminUser

logger = logging.getLogger(__name__)


class IsStudent(permissions.BasePermission):
    def has_permission(self, request, view):
        if not isinstance(request.user, StudentUser):
            return False

        if request.user and hasattr(request, 'service') and request.service == ServiceList.STUDENT.value:
            return True

        token_type = getattr(request.user, 'token_type', None)
        logger.warning(f"Student access denied for user: {request.user.email} (token_type: {token_type})")
        return False


class IsBankAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if not isinstance(request.user, BankAdminUser):
            return False

        # TODO: Need to gather more knowledge to implement that
        # if hasattr(request, 'auth_token') and request.auth_token:
        #     if not verify_supabase_jwt(request.auth_token):
        #         return False

        if request.user and hasattr(request, 'service') and request.service == ServiceList.BANK_ADMIN.value:
            return True

        # Check if user has token_type attribute (set by JWTAuth)
        token_type = getattr(request.user, 'token_type', None)

        if token_type == 'bank_admin':
            logger.info(f"Bank Admin access granted for user: {request.user.email}")
            return True

        logger.warning(f"Bank Admin access denied for user: {request.user.email} (token_type: {token_type})")
        return False


class IsStudentAdmin(permissions.BasePermission):
    """
    Permission class for admin users only
    """

    def has_permission(self, request, view):
        if not isinstance(request.user, CustomUser):
            return False

        if (request.user and request.user.is_authenticated and hasattr(request, 'service')
                and request.service == ServiceList.ADMIN.value):
            return True
        else:
            # Check if user has token_type attribute (set by JWTAuth)
            token_type = getattr(request.user, 'token_type', None)
            if token_type == 'local_admin':
                logger.info(f"Admin access granted for user: {request.user.username}")
                return True

            logger.warning(f"Admin access denied for user: {request.user.username} (token_type: {token_type})")
            return False


class IsPriyoPay(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.headers.get('x-api-key') == settings.PRIYOPAY_API_KEY


class IsAnyAdmin(permissions.BasePermission):
    """Combined permission for any type of admin - OR logic"""

    def has_permission(self, request, view):
        # Check if user is any type of admin (OR logic)
        bank_admin = IsBankAdmin()
        student_admin = IsStudentAdmin()
        priyo_pay = IsPriyoPay()

        return (bank_admin.has_permission(request, view) or
                student_admin.has_permission(request, view) or
                priyo_pay.has_permission(request, view))


def is_any_admin(request):
    return hasattr(request, 'service') and request.service in [ServiceList.ADMIN.value, ServiceList.BANK_ADMIN.value]
