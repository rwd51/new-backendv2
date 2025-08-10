import os
import re
import uuid
import logging
from django.conf import settings
from django.core.cache import cache
from storages.backends.gcloud import GoogleCloudStorage

logger = logging.getLogger(__name__)

def google_bucket_file_upload(the_file, file_name):
    """Upload file to GCP bucket - exact same as old backend"""
    try:
        error_msg = ""
        GoogleCloudStorage().save(name=file_name, content=the_file)
        return file_name, error_msg  # ✅ ADD THIS LINE

    except Exception as ex:
        error_msg = str(ex)
        file_name = None
        logger.error(error_msg, exc_info=True)

    return file_name, error_msg

def google_bucket_file_url(file_name):
    """Generate public URL - exact same as old backend"""
    cache_key = f"gs_url_{file_name}"
    cached_val = cache.get(cache_key)
    if cached_val:
        return cached_val
    try:
        ret = GoogleCloudStorage().url(file_name)
        print(f"GCP URL generated: {ret}")  # ✅ ADD THIS DEBUG LINE
    except Exception as ex:
        print(f"GCP URL error: {ex}")  # ✅ ADD THIS DEBUG LINE
        logger.error(str(ex), exc_info=True)
        ret = None
    cache.set(cache_key, ret, timeout=settings.GS_EXPIRATION.total_seconds())
    return ret

def google_bucket_file_delete(file_name):
    """Delete file from GCP - exact same as old backend"""
    try:
        return GoogleCloudStorage().delete(file_name)
    except Exception as ex:
        logger.error(str(ex), exc_info=True)
        return False

def build_file_name(upload_file, bucket_folder_name, version_required=True):
    """Build GCP file name - same logic as old backend"""
    name, extension = os.path.splitext(upload_file.name)
    bucket_file_name = re.sub('[^a-zA-Z0-9]', '_', name)
    max_char = getattr(settings, 'GS_BUCKET_FILE_NAME_MAX_CHAR', 50)
    if len(bucket_file_name) > max_char:
        bucket_file_name = bucket_file_name[:max_char]
    file_version = f"_v{str(uuid.uuid4())[:8]}" if version_required else ""
    file_name = bucket_folder_name + "/" + bucket_file_name + file_version + extension
    return file_name