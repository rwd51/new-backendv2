from rest_framework.viewsets import ModelViewSet
from rest_framework import status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.contrib.auth import get_user_model
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .utility.document_helper import google_bucket_file_upload, build_file_name

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'student-portal'))
from authentication import JWTAuth
from permissions import IsStudent, IsBankAdmin, IsStudentAdmin

from .models import *
from .serializers import *
from .filters import *

User = get_user_model()

from rest_framework.decorators import action
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

# Onboarding Step Management - matches old backend pattern
class OnboardingViewSet(APIView):
    """
    POST /onboarding/{step}/ - Save step data
    GET /onboarding/{step}/?user_id={userId} - Get step data
    """
    authentication_classes = [JWTAuth]
    permission_classes = [IsStudent | IsBankAdmin | IsStudentAdmin]
    
    def post(self, request, step):
        """Save step data"""
        step_data = request.data.get('data', {})
        is_completed = request.data.get('is_completed', True)
        
        # Validate step
        if step not in StudentOnboardingSteps.values():
            return Response({'error': 'Invalid step'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create the onboarding step
        onboarding_step, created = StudentOnboardingStep.objects.get_or_create(
            user=request.user,
            step=step,
            defaults={
                'step_data': step_data,
                'is_completed': is_completed
            }
        )
        
        if not created:
            # Update existing step
            onboarding_step.step_data.update(step_data)
            onboarding_step.is_completed = is_completed
            if is_completed:
                from django.utils import timezone
                onboarding_step.completed_at = timezone.now()
            onboarding_step.save()
        
        serializer = StudentOnboardingStepSerializer(onboarding_step)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    def get(self, request, step):
        """Get step data"""
        token_type = getattr(request.user, 'token_type', None)
        user_id = request.query_params.get('user_id')
        
        # Students can only see their own data
        if token_type == 'student':
            if user_id and user_id != str(request.user.id):
                return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
            target_user = request.user
        
        # Admins can see any user's data
        elif token_type == 'admin':
            if user_id:
                target_user = get_object_or_404(User, id=user_id)
            else:
                target_user = request.user
        else:
            return Response({'error': 'Invalid token type'}, status=status.HTTP_403_FORBIDDEN)
        
        # Validate step
        if step not in StudentOnboardingSteps.values():
            return Response({'error': 'Invalid step'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            onboarding_step = StudentOnboardingStep.objects.get(user=target_user, step=step)
            serializer = StudentOnboardingStepSerializer(onboarding_step)
            return Response(serializer.data)
        except StudentOnboardingStep.DoesNotExist:
            return Response({
                'step': step,
                'is_completed': False,
                'step_data': {},
                'message': 'Step not started yet'
            })

class OnboardingProgressViewSet(APIView):
    """GET /onboarding/progress/?user_id={userId} - Get onboarding progress"""
    authentication_classes = [JWTAuth]
    permission_classes = [IsStudent | IsBankAdmin | IsStudentAdmin]
    
    def get(self, request):
        """Get onboarding progress - matches old backend UserOnboardingFlowView"""
        token_type = getattr(request.user, 'token_type', None)
        user_id = request.query_params.get('user_id')
        
        # Students can only see their own progress
        if token_type == 'student':
            if user_id and user_id != str(request.user.id):
                return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
            target_user = request.user
        
        # Admins can see any user's progress
        elif token_type == 'admin':
            if user_id:
                target_user = get_object_or_404(User, id=user_id)
            else:
                target_user = request.user
        else:
            return Response({'error': 'Invalid token type'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get all onboarding steps for the user
        steps = StudentOnboardingStep.objects.filter(user=target_user)
        finished_steps = steps.values_list('step', flat=True)
        
        # Build response similar to old backend
        expected_steps = StudentOnboardingSteps.values()
        response = []
        
        for step in expected_steps:
            step_obj = steps.filter(step=step).first()
            response.append({
                'step': step,
                'finished': step in finished_steps,
                'is_completed': step_obj.is_completed if step_obj else False,
                'completed_at': step_obj.completed_at if step_obj else None,
                'step_data': step_obj.step_data if step_obj else {}
            })
        
        # Calculate progress percentage
        completed_steps = len([s for s in response if s['is_completed']])
        progress_percentage = (completed_steps / len(expected_steps) * 100) if expected_steps else 0
        
        return Response({
            'user_id': target_user.id,
            'progress_percentage': progress_percentage,
            'completed_steps': completed_steps,
            'total_steps': len(expected_steps),
            'steps': response
        })

class BaseStudentViewSet(ModelViewSet):
    """Base viewset with common functionality"""
    authentication_classes = [JWTAuth]
    permission_classes = [IsStudent | IsBankAdmin | IsStudentAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering = ['-created_at']
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return self.queryset.none()
        
        token_type = getattr(self.request.user, 'token_type', None)
        
        # Admin can see all records
        if token_type == 'admin':
            return self.queryset.all()
        
        # Student can only see their own records
        return self.queryset.filter(user=self.request.user)

# Education APIs - matches old backend /educations/
class EducationsViewSet(BaseStudentViewSet):
    """GET/POST/PATCH /educations/"""
    http_method_names = ['get', 'post', 'patch']
    queryset = StudentEducation.objects.all()
    serializer_class = StudentEducationSerializer
    filterset_class = UserEducationFilterSet
    search_fields = ['institution_name', 'degree', 'field_of_study']
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return self.queryset.none()
        
        token_type = getattr(self.request.user, 'token_type', None)
        user_id = self.request.query_params.get('user')  # ✅ ADD THIS
        
        if token_type == 'admin':
            if user_id:
                return self.queryset.filter(user_id=user_id)  # ✅ ADD THIS
            return self.queryset.all()
        
        return self.queryset.filter(user=self.request.user)

# Experience APIs - matches old backend /experiences/
class ExperiencesViewSet(BaseStudentViewSet):
    """GET/POST/PATCH /experiences/"""
    http_method_names = ['get', 'post', 'patch']
    queryset = StudentJobExperience.objects.all()
    serializer_class = StudentJobExperienceSerializer
    filterset_class = UserExperienceFilterSet
    search_fields = ['company_name', 'position']

# Student First Step APIs - matches old backend /student-first-step/
class StudentFirstStepViewSet(BaseStudentViewSet):
    """GET/POST/PATCH /student-first-step/ - Passport information"""
    http_method_names = ['get', 'post', 'patch']
    queryset = StudentPassport.objects.all()
    serializer_class = StudentPassportSerializer
    filterset_class = StudentPrimaryInfoFilterSet

# Foreign University APIs - matches old backend /foreign-universities/
class ForeignUniversitiesViewSet(BaseStudentViewSet):
    """GET/POST/PATCH /foreign-universities/"""
    http_method_names = ['get', 'post', 'patch']
    queryset = StudentForeignUniversity.objects.all()
    serializer_class = StudentForeignUniversitySerializer
    filterset_class = UserForeignUniversityFilterSet
    search_fields = ['university_name', 'country', 'program_name']

# Financial Information APIs - matches old backend /financial-info/
class FinancialInfoViewSet(BaseStudentViewSet):
    """GET/POST/PATCH /financial-info/"""
    http_method_names = ['get', 'post', 'patch']
    queryset = StudentFinancialInfo.objects.all()
    serializer_class = StudentFinancialInfoSerializer
    filterset_class = UserFinancialInfoFilterSet

# Financer APIs - matches old backend /financer-info/
class FinancerInfoViewSet(BaseStudentViewSet):
    """GET/POST/PATCH /financer-info/"""
    http_method_names = ['get', 'post', 'patch']
    queryset = StudentFinancerInfo.objects.all()
    serializer_class = StudentFinancerInfoSerializer
    filterset_class = UserFinancerInfoFilterSet
    search_fields = ['financer_name', 'relationship']


class StudentDocumentsViewSet(BaseStudentViewSet):
    """GET/POST/PATCH /student-documents/ - matches old backend"""
    http_method_names = ['get', 'post', 'patch']
    queryset = StudentDocument.objects.all()
    serializer_class = StudentDocumentSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return StudentDocumentUploadSerializer
        return StudentDocumentSerializer
    
    def create(self, request, *args, **kwargs):
        """Upload student documents - same logic as old backend"""
        serializer = StudentDocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        response_data, error_msg = self.upload_student_documents(
            serializer.validated_data, request.user
        )
        
        if error_msg:
            return Response({'Error': error_msg}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            data=StudentDocumentSerializer(response_data, many=True).data, 
            status=status.HTTP_200_OK
        )
    
    @classmethod
    def upload_student_documents(cls, validated_data, user):
        """Upload logic - adapted from old backend"""
        document_types = [
            'student_photograph', 'financer_photograph', 'student_signature', 
            'financer_signature', 'admission_letter', 'educational_certificate',
            'educational_transcript', 'university_invoice', 'financial_estimate',
            'language_test_result', 'other_documents'
        ]
        
        response_data = []
        error_message = ""
        
        try:
            for doc_type in document_types:
                uploaded_file = validated_data.get(doc_type)
                if uploaded_file:
                    # Build bucket path - same as old backend
                    bucket_folder_name = f"STUDENT/u{user.id}/{doc_type}"
                    file_name = build_file_name(uploaded_file, bucket_folder_name)
                    
                    # Upload to GCP
                    gcp_url, error_msg = google_bucket_file_upload(uploaded_file, file_name)
                    
                    if gcp_url:  # This is actually the file_name
                        # Create document record
                        document = StudentDocument.objects.create(
                            user=user,
                            document_type=doc_type,
                            original_filename=uploaded_file.name,
                            uploaded_file_name=gcp_url,  # ✅ Store the file path here
                            file_size=uploaded_file.size,
                            doc_type='STUDENT_DOCUMENTS',
                            related_resource_type='student'
                            # ✅ Remove gcp_url from here - let serializer generate it
                        )
                        response_data.append(document)
                        
            if len(response_data) == 0:
                error_message = "Failed to upload files!"
                
        except Exception as ex:
            error_message = str(ex)
        
        if len(response_data) > 0:  # If documents uploaded successfully
            # Auto-update onboarding progress
            from django.utils import timezone
            StudentOnboardingStep.objects.update_or_create(
                user=user,
                step='student_documents_upload',
                defaults={
                    'is_completed': True,
                    'completed_at': timezone.now(),
                    'step_data': {'documents_uploaded': len(response_data)}
                }
            )
        
        return response_data, error_message
    
# Student List & Detail APIs for Admin
# In students/viewsets.py - Replace the existing classes

# Student List & Detail APIs for Admin - FIXED
# In students/viewsets.py - Replace the StudentUsersViewSet class

class StudentUsersViewSet(ModelViewSet):  # Don't inherit from BaseStudentViewSet
    """GET /student-users/ - Student list for admin - matches old backend StudentUserViewSet"""
    http_method_names = ['get']
    permission_classes = [IsBankAdmin | IsStudentAdmin]
    authentication_classes = [JWTAuth]
    serializer_class = StudentUserSerializer
    search_fields = ['student_user__first_name', 'student_user__last_name', 'student_user__email']
    filterset_class = StudentUsersFilterSet
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering = ['-date_joined']  # User model has date_joined, not created_at
    
    def get_queryset(self):
        """Get users who have student_user records - matches old backend logic"""
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()
        
        # Get users who have StudentUser records (similar to student_primary_info in old backend)
        return User.objects.filter(student_user__isnull=False)
    
    def get_serializer_context(self):
        """Add profile image context like old backend"""
        context = super().get_serializer_context()
        context['include_profile_image_icon'] = True  # Admin can see profile images
        return context

# Complete Profile API for Admin - FIXED  
# In students/viewsets.py - ONLY replace the UserViewSet class
# Keep everything else unchanged

class UserViewSet(ModelViewSet):  # Don't inherit from BaseStudentViewSet
    """GET /user/{id}/ - Complete student profile for admin - matches old backend PriyoMoneyUserViewSet"""
    http_method_names = ['get', 'patch']
    permission_classes = [IsBankAdmin | IsStudentAdmin]
    authentication_classes = [JWTAuth]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering = ['-date_joined']  # User model has date_joined, not created_at
    
    def get_queryset(self):
        """Get all users - admin can access any user"""
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()
        return User.objects.all()
    
    def get_serializer_class(self):
        """Return complete profile serializer"""
        return StudentCompleteProfileSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """Get complete student profile - matches old backend logic"""
        user = self.get_object()
        
        # Check if user has student profile
        try:
            student_user = user.student_user
        except:
            # Create minimal StudentUser if doesn't exist (auto-create pattern)
            student_user = StudentUser.objects.create(
                user=user,
                first_name=user.first_name or 'Student',
                last_name=user.last_name or f'#{user.id}',
                email=user.email or f'student_{user.id}@temp.com',
            )
        
        serializer = StudentCompleteProfileSerializer(student_user, context={'request': request})
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """Update student profile - admin only"""
        user = self.get_object()
        
        try:
            student_user = user.student_user
        except:
            return Response({'error': 'Student profile not found'}, status=404)
        
        serializer = StudentCompleteProfileSerializer(
            student_user, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)

# Address Management for Admin
class UserAddressViewSet(BaseStudentViewSet):
    """GET/PATCH /user-address/ - Address management"""
    http_method_names = ['get', 'post', 'patch']
    permission_classes = [IsStudent| IsBankAdmin | IsStudentAdmin]
    queryset = StudentAddress.objects.all()
    serializer_class = StudentAddressSerializer
    filterset_fields = ['address_type', 'user']