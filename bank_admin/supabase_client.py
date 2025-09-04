from django.conf import settings
from supabase import create_client, Client


supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
