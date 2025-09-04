from rest_framework.routers import SimpleRouter
from django.urls import path, include

from student_admin.viewsets import BdBankViewSet

router = SimpleRouter(trailing_slash=True)
router.register(r'bd-bank', BdBankViewSet, basename='bd-bank')

urlpatterns = [
    path('', include(router.urls)),
]
