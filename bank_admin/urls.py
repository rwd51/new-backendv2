from rest_framework.routers import SimpleRouter
from django.urls import path, include
from bank_admin.views import AuthViewSet, BankAdminApprovalViewSet, BankAdminListViewSet

app_name = 'bank_admin'

router = SimpleRouter(trailing_slash=True)
auth_view_set = AuthViewSet.as_view({'post': 'signup'})
login_view_set = AuthViewSet.as_view({'post': 'signin'})
refresh_view_set = AuthViewSet.as_view({"post": "refresh"})
logout_view_set = AuthViewSet.as_view({"post": "logout"})

router.register(r'admin-approval', BankAdminApprovalViewSet, basename='bank-admin-approval')
router.register(r'admins', BankAdminListViewSet, basename='bank-admins')

urlpatterns = [
    path('', include(router.urls)),
    path("auth/signup/", auth_view_set, name="bank-admin-signup"),
    path("auth/signin/", login_view_set, name="bank-admin-signin"),
    path("auth/refresh/", refresh_view_set, name="bank-admin-refresh-token"),
    path("auth/logout/", logout_view_set, name="bank-admin-logout"),
]
