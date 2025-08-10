from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

# Swagger Configuration
schema_view = get_schema_view(
    openapi.Info(
        title="Student Backend API",
        default_version='v1',
        description="Student Management Microservice API",
        terms_of_service="https://www.yourcompany.com/terms/",
        contact=openapi.Contact(email="admin@yourcompany.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    patterns=[
        path('', include('students.urls')),
    ],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Routes - students URLs will be directly accessible
    path('', include('students.urls')),
    
    # Swagger Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)