from rest_framework import permissions
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
        
        if token_type == 'admin':
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
        
        if token_type == 'admin':
            logger.info(f"Admin access granted for user: {request.user.username}")
            return True
        
        logger.warning(f"Admin access denied for user: {request.user.username} (token_type: {token_type})")
        return False
