from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

# Import admin auth views
from .admin_auth import admin_register, admin_login, admin_logout, AdminTokenRefreshView

# Swagger Configuration
schema_view = get_schema_view(
    openapi.Info(
        title="Student Backend API",
        default_version='v1',
        description="Student Management Micro-service API",
        terms_of_service="https://www.priyo.com/terms/",
        contact=openapi.Contact(email="admin@priyo.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny,],
    patterns=[
        path('', include('students.urls')),
        path('', include('bank_admin.urls')),
        path('', include('student_admin.urls')),
    ],
)

urlpatterns = [
    # ✅ PUT CUSTOM ADMIN ENDPOINTS FIRST (before Django admin)
    path('admin/register/', admin_register, name='admin_register'),
    path('admin/login/', admin_login, name='admin_login'),
    path('admin/login/refresh/', AdminTokenRefreshView.as_view(), name='admin_token_refresh'),
    path('admin/logout/', admin_logout, name='admin_logout'),
    
    # ✅ Django admin AFTER your custom endpoints
    path('admin/', admin.site.urls),
    
    # API Routes
    path('', include('students.urls')),
    path('health/', include('health.urls')),
    path('bank-admin/', include('bank_admin.urls')),
    path('', include('student_admin.urls')),

    # Swagger Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)