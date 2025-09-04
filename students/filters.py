from django_filters.rest_framework import FilterSet
from .models import *

from django_filters.rest_framework import FilterSet, BooleanFilter, CharFilter
from django.contrib.auth import get_user_model
from .models import *

# User = get_user_model()


class UserEducationFilterSet(FilterSet):
    class Meta:
        model = StudentEducation
        fields = ['is_current', 'degree']


class UserExperienceFilterSet(FilterSet):
    class Meta:
        model = StudentJobExperience
        fields = ['is_current', 'position']


class StudentPrimaryInfoFilterSet(FilterSet):
    class Meta:
        model = StudentPassport
        fields = ['passport_issue_place']  # ✅ Use the correct field name


class UserForeignUniversityFilterSet(FilterSet):
    class Meta:
        model = StudentForeignUniversity
        fields = ['country', 'degree_level']


class UserFinancialInfoFilterSet(FilterSet):
    class Meta:
        model = StudentFinancialInfo
        fields = ['bank_statement_available']


class UserFinancerInfoFilterSet(FilterSet):
    class Meta:
        model = StudentFinancerInfo
        fields = ['is_primary_financer', 'relationship']


class StudentUsersFilterSet(FilterSet):
    """Filter for student users - handles StudentUser model fields"""

    # is_approved = BooleanFilter(field_name='student_user__is_approved')
    # nationality = CharFilter(field_name='student_user__nationality', lookup_expr='icontains')
    # is_active = BooleanFilter(field_name='student_user__is_active')
    # first_name = CharFilter(field_name='student_user__first_name', lookup_expr='icontains')
    # last_name = CharFilter(field_name='student_user__last_name', lookup_expr='icontains')
    # email = CharFilter(field_name='student_user__email', lookup_expr='icontains')

    class Meta:
        model = StudentUser
        fields = ['is_approved', 'nationality', 'is_active', 'first_name', 'last_name', 'email']
