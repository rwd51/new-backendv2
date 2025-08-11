import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def admin_register(request):
    """
    POST /admin/register/
    Pure Django view - NO DRF, NO CSRF
    """
    print("🚀🚀🚀 ADMIN REGISTER VIEW CALLED!")
    print(f"Request method: {request.method}")
    print(f"Request path: {request.path}")
    try:
        # Parse JSON data
        data = json.loads(request.body.decode('utf-8'))
        
        username = data.get('username')
        password = data.get('password')
        admin_type = data.get('admin_type', 'bank_admin')
        email = data.get('email', f'{username}@adminportal.com')
        first_name = data.get('first_name', 'Admin')
        last_name = data.get('last_name', 'User')
        
        if not username or not password:
            return JsonResponse({
                'error': 'Username and password are required'
            }, status=400)
        
        if admin_type not in ['bank_admin', 'student_admin']:
            return JsonResponse({
                'error': 'admin_type must be bank_admin or student_admin'
            }, status=400)
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                'error': 'Username already exists'
            }, status=400)
        
        # Create admin user
        admin_user = User.objects.create(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=make_password(password),
            admin_type=admin_type,
            is_staff=True,
            is_active=True
        )
        
        logger.info(f"{admin_type} user created: {username}")
        
        return JsonResponse({
            'message': f'{admin_type} user created successfully',
            'user_id': admin_user.id,
            'username': username,
            'admin_type': admin_type
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Admin registration failed: {e}")
        return JsonResponse({'error': 'Registration failed'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def admin_login(request):
    """
    POST /admin/login/
    Pure Django view - NO DRF, NO CSRF
    """
    try:
        # Parse JSON data
        data = json.loads(request.body.decode('utf-8'))
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return JsonResponse({
                'error': 'Username and password are required'
            }, status=400)
        
        # Authenticate user
        user = authenticate(username=username, password=password)
        
        if user is None:
            return JsonResponse({
                'error': 'Invalid credentials'
            }, status=401)
        
        if not user.is_active:
            return JsonResponse({
                'error': 'Account is disabled'
            }, status=401)
        
        # Check if user is admin
        if not (user.admin_type or user.is_staff):
            return JsonResponse({
                'error': 'Not authorized as admin'
            }, status=403)
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        # Add custom claims to match old backend format
        refresh['username'] = user.username
        refresh['email'] = user.email
        refresh['user_id'] = user.id
        
        access = refresh.access_token
        access['username'] = user.username
        access['email'] = user.email
        access['user_id'] = user.id
        
        logger.info(f"Admin login successful: {username}")
        
        return JsonResponse({
            'refresh': str(refresh),
            'access': str(access)
        }, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Admin login failed: {e}")
        return JsonResponse({'error': 'Login failed'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def admin_logout(request):
    """
    POST /admin/logout/
    Pure Django view - NO DRF, NO CSRF
    """
    try:
        # Parse JSON data
        data = json.loads(request.body.decode('utf-8'))
        
        refresh_token = data.get('refresh')
        
        if not refresh_token:
            return JsonResponse({
                'error': 'Refresh token is required'
            }, status=400)
        
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            pass  # Token might already be blacklisted or invalid
        
        logger.info(f"Admin logout successful")
        
        return JsonResponse({
            'message': 'Logout successful'
        }, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Admin logout failed: {e}")
        return JsonResponse({'error': 'Logout failed'}, status=500)

# For token refresh, we'll use DRF's view but with CSRF exempt
from django.utils.decorators import method_decorator
from rest_framework_simplejwt.views import TokenRefreshView

@method_decorator(csrf_exempt, name='dispatch')
class AdminTokenRefreshView(TokenRefreshView):
    """
    POST /admin/login/refresh/
    """
    pass