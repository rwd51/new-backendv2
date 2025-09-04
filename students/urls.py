from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter

from students.views import DepositClaimsView, BDTtoUSDView, USDAccountsView, CurrencyConversionView, \
    BDTUSDConversionView
from students.viewsets import *

router = DefaultRouter()

# Register with exact endpoint names from old backend
router.register(r'educations', EducationsViewSet, basename='educations')
router.register(r'experiences', ExperiencesViewSet, basename='experiences')
router.register(r'student-first-step', StudentFirstStepViewSet, basename='student_first_step')
router.register(r'foreign-universities', ForeignUniversitiesViewSet, basename='foreign_universities')
router.register(r'financial-info', FinancialInfoViewSet, basename='financial_info')
router.register(r'financer-info', FinancerInfoViewSet, basename='financer_info')

router.register(r'student-documents', StudentDocumentsViewSet, basename='student_documents')
router.register(r'student-users', StudentUsersViewSet, basename='student_users')
router.register(r'user', UserViewSet, basename='user')
router.register(r'user-address', UserAddressViewSet, basename='user_address')

urlpatterns = [
    path('', include(router.urls)),

    path('onboarding/progress/', OnboardingProgressViewSet.as_view(), name='onboarding_progress'),
    path('deposits/', DepositClaimsView.as_view(), name='deposits'),
    path('deposits/<str:pk>/', DepositClaimsView.as_view(), name='deposit_detail'),  # ADD THIS
    path('conversions/', BDTtoUSDView.as_view(), name='conversions'),
    path('conversions/<str:pk>/', BDTtoUSDView.as_view(), name='conversion_detail'),
    path('usd-accounts/', USDAccountsView.as_view(), name='usd_accounts'),
    path('usd-accounts/<str:user_id>/', USDAccountsView.as_view(), name='usd_accounts_detail'),
    path('convert-currency/', CurrencyConversionView.as_view(), name='convert_currency'),
    path('bdt-usd-conversion/', BDTUSDConversionView.as_view(), name='bdt_usd_conversion'),
    path('bdt-usd-conversion/<str:pk>/', BDTUSDConversionView.as_view(), name='bdt_usd_conversion_detail'),

    re_path(r'^onboarding/(?P<step>[\w-]+)/$', OnboardingViewSet.as_view(), name='onboarding_step'),
]
