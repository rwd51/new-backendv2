import requests
import logging

from django.conf import settings
from jose import jwt
from bank_admin.supabase_client import supabase
from rest_framework.permissions import BasePermission

logger = logging.getLogger(__name__)
JWKS_URL = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
jwks = requests.get(JWKS_URL).json()


class IsSupabaseAuthenticated(BasePermission):
    def has_permission(self, request, view):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return False

        token = auth_header.split(" ")[1]
        try:
            # Verify signature using JWKS
            header = jwt.get_unverified_header(token)
            key = next((k for k in jwks["keys"] if k["kid"] == header["kid"]), None)
            if key is None:
                return False

            jwt.decode(
                token,
                key,
                algorithms=[header["alg"]],
                options={"verify_aud": False}  # adjust as needed
            )
            return True
        except Exception:
            return False


def verify_supabase_jwt(token: str):
    try:
        header = supabase.auth.get_claims(jwt=token)
        key = next((k for k in jwks["keys"] if k["kid"] == header["kid"]), None)
        if not key:
            return None

        decoded = jwt.decode(token, key, algorithms=[header["alg"]], options={"verify_aud": False})
        return decoded
    except Exception as ex:
        logger.warning(f"Supabase JWT token validation error: {ex}")
        return None
