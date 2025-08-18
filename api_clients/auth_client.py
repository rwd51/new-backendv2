# student_portal/auth_client.py

import requests
import logging
from django.conf import settings
from typing import Optional, Dict, Any

log = logging.getLogger(__name__)

class AuthServiceClient:
    """
    Client to interact with external auth service
    """
    
    def __init__(self):
        self.base_url = getattr(settings, 'AUTH_API_BASE')
        self.api_key = getattr(settings, 'AUTH_API_KEY')
        self.timeout = 30
        
        if not self.base_url or not self.api_key:
            raise ValueError("AUTH_API_BASE and AUTH_API_KEY must be set in environment variables")
    
    def get_user_profile(self, jwt_token: str) -> Optional[Dict[Any, Any]]:
        """
        Fetch user profile from auth service using JWT token
        
        Args:
            jwt_token (str): The JWT token from Authorization header
            
        Returns:
            dict: User profile data or None if failed
        """
        try:
            url = f"{self.base_url}/auth/api/v1/user-profile/"
            
            headers = {
                'Authorization': f'Token {jwt_token}',
                'APIKEY': self.api_key,
                'Content-Type': 'application/json'
            }
            
            log.info(f"Fetching user profile from auth service: {url}")
            
            response = requests.get(
                url,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                profile_data = response.json()
                log.info(f"Successfully fetched user profile for user ID: {profile_data.get('id')}")
                return profile_data
            
            elif response.status_code == 401:
                log.warning("Auth service returned 401 - Invalid or expired token")
                return None
                
            elif response.status_code == 404:
                log.warning("Auth service returned 404 - User not found")
                return None
                
            else:
                log.error(f"Auth service returned {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            log.error("Auth service request timed out")
            return None
            
        except requests.exceptions.ConnectionError:
            log.error("Failed to connect to auth service")
            return None
            
        except requests.exceptions.RequestException as e:
            log.error(f"Auth service request failed: {e}")
            return None
            
        except Exception as e:
            log.error(f"Unexpected error fetching user profile: {e}")
            return None
    
    def extract_user_details(self, profile_data: Dict[Any, Any]) -> Dict[str, Any]:
        """
        Extract and format user details from auth service response
        
        Args:
            profile_data (dict): Raw response from auth service
            
        Returns:
            dict: Formatted user details
        """
        try:
            # Extract from main user object
            user_data = profile_data
            profile = profile_data.get('profile', {})
            
            # Extract name from profile.name or use first_name/last_name
            full_name = profile.get('name', '').strip()
            first_name = user_data.get('first_name', '').strip()
            last_name = user_data.get('last_name', '').strip()
            
            # Parse full name if first_name/last_name are empty
            if not first_name and not last_name and full_name:
                name_parts = full_name.split(' ', 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            # Fallback if still empty
            if not first_name:
                first_name = "User"
            if not last_name:
                last_name = f"{user_data.get('id', 'Unknown')}"
            
            return {
                'auth_user_id': user_data.get('id'),
                'uuid': user_data.get('uid'),  # Note: 'uid' in response, not 'uuid'
                'username': user_data.get('username'),
                'email': user_data.get('email'),
                'first_name': first_name,
                'last_name': last_name,
                'mobile': user_data.get('mobile'),
                'is_active': user_data.get('is_active', True),
                'is_email_verified': user_data.get('is_email_verified', False),
                'is_mobile_verified': user_data.get('is_mobile_verified', False),
                'date_joined': user_data.get('date_joined'),
                'last_login': user_data.get('last_login'),
                
                # Profile specific data
                'profile_id': profile.get('id'),
                'image': profile.get('image'),
                'father_name': profile.get('father_name'),
                'mother_name': profile.get('mother_name'),
                'dob': profile.get('dob'),
                'gender': profile.get('gender'),
                'religion': profile.get('religion'),
                'marital_status': profile.get('marital_status'),
                'nid': profile.get('nid'),
                'nationality': profile.get('nationality'),
                'organization': profile.get('organization'),
                'about_me': profile.get('about_me'),
                'facebook_link': profile.get('facebook_link'),
                'linkedin_link': profile.get('linkedin_link'),
            }
            
        except Exception as e:
            log.error(f"Error extracting user details: {e}")
            return {}

# Create a singleton instance
auth_client = AuthServiceClient()