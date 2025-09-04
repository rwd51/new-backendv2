import logging
import jwt

from django.utils import timezone
from rest_framework import authentication, exceptions
from api_clients.auth_client import auth_client
from students.models import CustomUser, StudentUser

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
            decoded_token = jwt.decode(auth_token, options={"verify_signature": False})
            return auth_token, decoded_token
        except jwt.exceptions.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid token')

    @staticmethod
    def determine_token_type(decoded_token):
        """
        Determine if token is for student or admin based on token structure
        """
        user_metadata = decoded_token.get('user_metadata', {})
        if user_metadata.get('email') and user_metadata.get('email_verified') and user_metadata.get('sub'):
            return 'bank_admin'
        # Local admin tokens have token_type, exp, iat, user_id, username, email (from JWT)
        elif 'token_type' in decoded_token and 'username' in decoded_token and 'email' in decoded_token and 'user_id' in decoded_token:
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

    @staticmethod
    def get_or_create_student_from_token(student_details, jwt_token):
        """
        Get or create student user from token data
        Uses auth service to fetch real user details
        """
        auth_uuid = student_details.get('uuid')
        student_id = student_details.get('id')

        if not auth_uuid:
            raise exceptions.AuthenticationFailed('Invalid student token payload - missing uuid')

        # Try to find existing user by one_auth_uuid
        try:
            user = StudentUser.objects.get(one_auth_uuid=auth_uuid)
            log.info(f"Found existing student user: {user.id}")
            return user
        except StudentUser.DoesNotExist:
            log.info(f"Creating new student user for UUID: {auth_uuid}")

            # Fetch user details from auth service
            profile_data = auth_client.get_user_profile(jwt_token)

            if not profile_data:
                raise exceptions.AuthenticationFailed('Failed to fetch user profile from auth service')

            # Extract user details from auth service response
            user_details = auth_client.extract_user_details(profile_data)

            if not user_details:
                raise exceptions.AuthenticationFailed('Failed to extract user details from auth service response')

            log.info(
                f"Successfully fetched user details from auth service for user ID: {user_details.get('auth_user_id')}")

            user = StudentUser.objects.create(
                first_name=user_details.get('first_name', 'User'),
                last_name=user_details.get('last_name', f'User{student_id}'),
                email=user_details.get('email', f'user{student_id}@example.com'),
                mobile_number=user_details.get('mobile'),
                date_of_birth=user_details.get('dob'),
                gender=user_details.get('gender'),
                nationality=user_details.get('nationality'),
                is_active=True,
            )

            log.info(f"Created new student user with real data: {user_details.get('first_name')} "
                     f"{user_details.get('last_name')} ({user_details.get('email')})")
            return user

    @staticmethod
    def get_admin_from_token(admin_details):
        user_id = admin_details.get('user_id')
        username = admin_details.get('username')

        if not user_id:
            raise exceptions.AuthenticationFailed('Invalid local admin token payload - missing user_id')

        try:
            user = CustomUser.objects.get(id=user_id, username=username)
            if not (user.admin_type or user.is_staff):
                raise exceptions.AuthenticationFailed('User is not an admin')

            return user
        except CustomUser.DoesNotExist:
            raise exceptions.AuthenticationFailed('Admin user not found in local database')

    @staticmethod
    def get_bank_admin_from_token(admin_details):
        from bank_admin.models import BankAdminUser

        user_id = admin_details.get('user_id')
        email = admin_details.get('email')

        if not user_id or not email:
            raise exceptions.AuthenticationFailed('Invalid bank admin token payload - missing user_id or email')

        try:
            user = BankAdminUser.objects.get(user_id=user_id, email=email)
            if not user.is_active:
                raise exceptions.AuthenticationFailed('Bank Admin user is not active')

            return user
        except BankAdminUser.DoesNotExist:
            raise exceptions.AuthenticationFailed('Bank Admin user not found in Student Portal')

    def authenticate(self, request):
        """
        Main authentication method that handles both student and admin tokens
        """
        try:
            token, decoded_token = self.retrieve_jwt_token_from_request(request)
        except exceptions.AuthenticationFailed:
            return None

        try:
            token_type = self.determine_token_type(decoded_token)
        except exceptions.AuthenticationFailed as e:
            log.warning(f'Unknown JWT token format: {e}')
            return None

        current_time = timezone.now().timestamp()

        if token_type == 'student':
            if self.has_student_token_expired(decoded_token, current_time):
                raise exceptions.AuthenticationFailed('Student token has expired')
        elif token_type in ['local_admin', 'bank_admin']:
            if self.has_admin_token_expired(decoded_token, current_time):
                raise exceptions.AuthenticationFailed('Admin token has expired')

        try:
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
                user = self.get_admin_from_token(user_details)
            elif token_type == 'bank_admin':
                user_metadata = decoded_token.get('user_metadata', {})
                user_details = {
                    'user_id': user_metadata.get('sub'),
                    'email': user_metadata.get('email')
                }
                user = self.get_bank_admin_from_token(user_details)
            else:
                raise exceptions.AuthenticationFailed('Unsupported token type')

            if not user.is_active:
                raise exceptions.AuthenticationFailed('User is inactive')

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
