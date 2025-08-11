from rest_framework import permissions
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class IsStudent(permissions.BasePermission):
    """
    Permission class for student users only
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has token_type attribute (set by JWTAuth)
        token_type = getattr(request.user, 'token_type', None)
        
        if token_type == 'student':
            logger.info(f"Student access granted for user: {request.user.username}")
            return True
        
        logger.warning(f"Student access denied for user: {request.user.username} (token_type: {token_type})")
        return False
    
## for now both admin implementations will be same

class IsBankAdmin(permissions.BasePermission):
    """
    Permission class for admin users only
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has token_type attribute (set by JWTAuth)
        token_type = getattr(request.user, 'token_type', None)
        
        if token_type == 'local_admin':
            logger.info(f"Admin access granted for user: {request.user.username}")
            return True
        
        logger.warning(f"Admin access denied for user: {request.user.username} (token_type: {token_type})")
        return False

class IsStudentAdmin(permissions.BasePermission):
    """
    Permission class for admin users only
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
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
