import logging
import jwt
import random
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import authentication, exceptions
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()
log = logging.getLogger(__name__)

class JWTAuth(authentication.BaseAuthentication):
    """
    JWT authentication that handles both student and admin tokens
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
            raise exceptions.AuthenticationFailed('Unknown token format')

    @staticmethod
    def has_student_token_expired(token, current_time):
        """
        Check if student token has expired
        """
        created_at = token.get('created_at')
        expired_at = token.get('expired_at')
        
        if not created_at or not expired_at:
            return True
        
        return not (created_at <= current_time < expired_at)

    @staticmethod
    def has_admin_token_expired(token, current_time):
        """
        Check if admin token has expired
        """
        exp = token.get('exp')
        if not exp:
            return True
        
        return current_time >= exp

    @staticmethod
    def generate_mock_student_data(student_id, uuid):
        """Generate consistent mock data for students"""
        # Use student_id for consistent names
        student_num = student_id or (hash(str(uuid)) % 9999)
        
        first_names = ['Tom', 'Sarah', 'John', 'Emma', 'Mike', 'Lisa', 'David', 'Anna']
        last_names = ['Khan', 'Rahman', 'Ahmed', 'Hossain', 'Islam', 'Begum', 'Ali', 'Sheikh']
        
        # Use hash for consistent selection
        random.seed(hash(str(uuid)))
        first_name = f"{random.choice(first_names)}{student_num}"
        last_name = random.choice(last_names)
        email = f"student_{student_num}@yopmail.com"
        
        return first_name, last_name, email

    @staticmethod
    def generate_mock_admin_data(username):
        """Generate consistent mock data for admins"""
        admin_first_names = ['Admin', 'Manager', 'Director', 'Chief']
        admin_last_names = ['Operations', 'Review', 'Support', 'Control']
        
        # Use username hash for consistency
        hash_val = abs(hash(username)) % 1000
        random.seed(hash(username))
        first_name = f"{random.choice(admin_first_names)}{hash_val}"
        last_name = random.choice(admin_last_names)
        email = f"{username}@adminportal.yopmail.com"
        
        return first_name, last_name, email

    def get_or_create_student_from_token(self, student_details):
        """Get or create student user from token data"""
        uuid = student_details.get('uuid')
        student_id = student_details.get('id')
        
        if not uuid:
            raise exceptions.AuthenticationFailed('Invalid student token payload - missing uuid')

        # Try to find existing user by one_auth_uuid
        try:
            user = User.objects.get(one_auth_uuid=uuid)
        except User.DoesNotExist:
            # Generate mock data
            first_name, last_name, email = self.generate_mock_student_data(student_id, uuid)
            
            # Create user record with mock data
            user = User.objects.create(
                username=str(uuid)[:30],  # Truncate for Django compatibility
                first_name=first_name,
                last_name=last_name,
                email=email,
                one_auth_uuid=uuid,
                is_active=True,
                is_staff=False,
                is_superuser=False
            )
            
            # Auto-create StudentUser with better mock data
            from students.models import StudentUser
            StudentUser.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                email=email,
                mobile_number=f"+880171234{student_id or abs(hash(str(uuid))) % 10000}",
                nationality="Bangladesh",
                is_active=True
            )
            
            log.info(f"Created new student user: {first_name} {last_name} ({email})")

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
            # Get or create user based on token type
            if token_type == 'student':
                user_details = {
                    'uuid': decoded_token.get('uuid'),
                    'id': decoded_token.get('id'),
                    'device_type': decoded_token.get('device_type'),
                    'device_id': decoded_token.get('device_id')
                }
                user = self.get_or_create_student_from_token(user_details)
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