from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Student Portal API",
        default_version='v1',
        description="API documentation for Student Portal",
    ),
    public=True,
    authentication_classes=[],
    permission_classes=[permissions.AllowAny, ],
)
