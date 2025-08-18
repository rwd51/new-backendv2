# student_portal/authentication.py

import logging
import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import authentication, exceptions
from rest_framework.exceptions import AuthenticationFailed

# Import our new auth client
from api_clients.auth_client import auth_client

User = get_user_model()
log = logging.getLogger(__name__)

class JWTAuth(authentication.BaseAuthentication):
    """
    JWT authentication that handles both student and admin tokens
    Now with proper auth service integration for student users
    """

    @staticmethod
    def retrieve_jwt_token_from_request(request):
        """
        Extract JWT token from request header
        """
        PREFIX = 'Bearer '
        auth_header = request.META.get('HTTP_AUTHORIZATION')

        if auth_header is None:
            raise exceptions.AuthenticationFailed('Authorization header missing')

        if not auth_header.startswith(PREFIX):
            raise exceptions.AuthenticationFailed('Bearer prefix missing in authorization header')

        auth_token = auth_header[len(PREFIX):]
        try:
            # Decode without signature verification
            decoded_token = jwt.decode(auth_token, options={"verify_signature": False})
            return auth_token, decoded_token
        except jwt.exceptions.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid token')

    @staticmethod
    def determine_token_type(decoded_token):
        """
        Determine if token is for student or admin based on token structure
        """
        # Local admin tokens have token_type, exp, iat, user_id, username, email (from JWT)
        if 'token_type' in decoded_token and 'username' in decoded_token and 'email' in decoded_token and 'user_id' in decoded_token:
            return 'local_admin'
        # Student tokens have created_at, expired_at, id, uuid, device_type
        elif 'uuid' in decoded_token and 'created_at' in decoded_token and 'expired_at' in decoded_token:
            return 'student'
        else:
            raise exceptions.AuthenticationFailed('Unknown token type')

    @staticmethod
    def has_student_token_expired(decoded_token, current_time):
        """Check if student token has expired"""
        expired_at = decoded_token.get('expired_at')
        if expired_at and current_time > expired_at:
            return True
        return False

    @staticmethod
    def has_admin_token_expired(decoded_token, current_time):
        """Check if admin token has expired"""
        exp = decoded_token.get('exp')
        if exp and current_time > exp:
            return True
        return False



    def get_or_create_student_from_token(self, student_details, jwt_token):
        """
        Get or create student user from token data
        Uses auth service to fetch real user details
        """
        uuid = student_details.get('uuid')
        student_id = student_details.get('id')
        
        if not uuid:
            raise exceptions.AuthenticationFailed('Invalid student token payload - missing uuid')

        # Try to find existing user by one_auth_uuid
        try:
            user = User.objects.get(one_auth_uuid=uuid)
            log.info(f"Found existing student user: {user.id}")
            return user
        except User.DoesNotExist:
            log.info(f"Creating new student user for UUID: {uuid}")
            
            # Fetch user details from auth service
            profile_data = auth_client.get_user_profile(jwt_token)
            
            if not profile_data:
                raise exceptions.AuthenticationFailed('Failed to fetch user profile from auth service')
            
            # Extract user details from auth service response
            user_details = auth_client.extract_user_details(profile_data)
            
            if not user_details:
                raise exceptions.AuthenticationFailed('Failed to extract user details from auth service response')
            
            log.info(f"Successfully fetched user details from auth service for user ID: {user_details.get('auth_user_id')}")
            
            # Create user with real data from auth service
            user = User.objects.create(
                username=str(uuid)[:30],  # Truncate for Django compatibility
                first_name=user_details.get('first_name', 'User'),
                last_name=user_details.get('last_name', f'User{student_id}'),
                email=user_details.get('email', f'user{student_id}@example.com'),
                one_auth_uuid=uuid,
                is_active=user_details.get('is_active', True),
                is_staff=False,
                is_superuser=False
            )
            
            # Auto-create StudentUser with real data from auth service (only actual model fields)
            from students.models import StudentUser
            StudentUser.objects.create(
                user=user,
                first_name=user_details.get('first_name', 'User'),
                last_name=user_details.get('last_name', f'User{student_id}'),
                email=user_details.get('email', f'user{student_id}@example.com'),
                mobile_number=user_details.get('mobile'),  # This can be None, model allows it
                date_of_birth=user_details.get('dob'),  # This can be None, model allows it  
                gender=user_details.get('gender'),  # This can be None, model allows it
                nationality=user_details.get('nationality'),  # This can be None, model allows it
                priyopay_id=None,  # Will be set later when needed
                is_active=True,
                is_approved=False,  # New users start unapproved
                approved_by=None,
                approved_at=None,
            )
            
            log.info(f"Created new student user with real data: {user_details.get('first_name')} {user_details.get('last_name')} ({user_details.get('email')})")
            return user

    def get_or_create_local_admin_from_token(self, admin_details):
        """Get admin user from local database"""
        user_id = admin_details.get('user_id')
        username = admin_details.get('username')
        
        if not user_id:
            raise exceptions.AuthenticationFailed('Invalid local admin token payload - missing user_id')
            
        try:
            # Get admin from local database
            user = User.objects.get(id=user_id, username=username)
            
            if not (user.admin_type or user.is_staff):
                raise exceptions.AuthenticationFailed('User is not an admin')
                
            return user
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('Admin user not found in local database')

    def authenticate(self, request):
        """
        Main authentication method that handles both student and admin tokens
        """
        try:
            token, decoded_token = self.retrieve_jwt_token_from_request(request)
        except exceptions.AuthenticationFailed:
            return None

        # Determine token type
        try:
            token_type = self.determine_token_type(decoded_token)
        except exceptions.AuthenticationFailed as e:
            log.warning(f'Unknown token format: {e}')
            return None

        current_time = timezone.now().timestamp()

        if token_type == 'student':
            if self.has_student_token_expired(decoded_token, current_time):
                raise exceptions.AuthenticationFailed('Student token has expired')
        elif token_type == 'local_admin':
            if self.has_admin_token_expired(decoded_token, current_time):
                raise exceptions.AuthenticationFailed('Admin token has expired')

        try:
            # Get or create user based on token type
            if token_type == 'student':
                user_details = {
                    'uuid': decoded_token.get('uuid'),
                    'id': decoded_token.get('id'),
                    'device_type': decoded_token.get('device_type'),
                    'device_id': decoded_token.get('device_id')
                }
                # Pass the original JWT token to fetch from auth service
                user = self.get_or_create_student_from_token(user_details, token)
            elif token_type == 'local_admin':
                user_details = {
                    'user_id': decoded_token.get('user_id'),
                    'username': decoded_token.get('username'),
                    'email': decoded_token.get('email')
                }
                user = self.get_or_create_local_admin_from_token(user_details)
            else:
                raise exceptions.AuthenticationFailed('Unsupported token type')
            
            if not user.is_active:
                raise exceptions.AuthenticationFailed('User is inactive')

            # Add token type to user object for later use in views
            user.token_type = token_type
            user.token_data = decoded_token

            return user, token

        except Exception as ex:
            log.error(f'Authentication failed: {ex}', exc_info=True)
            raise exceptions.AuthenticationFailed(f'User authentication failed: {ex}')


class NoAuth(authentication.BaseAuthentication):
    """
    No authentication class for public endpoints
    """
    def authenticate(self, request):
        return None