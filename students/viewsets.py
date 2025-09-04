import logging

from rest_framework.views import APIView
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from rest_framework.viewsets import ModelViewSet
from rest_framework import status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from student_portal.authentication import JWTAuth
from students.enums import StudentOnboardingSteps
from students.filters import UserEducationFilterSet, UserExperienceFilterSet, StudentPrimaryInfoFilterSet, \
    UserForeignUniversityFilterSet, UserFinancialInfoFilterSet, UserFinancerInfoFilterSet, StudentUsersFilterSet
from students.models import StudentOnboardingStep, StudentEducation, StudentJobExperience, StudentPassport, \
    StudentForeignUniversity, StudentFinancialInfo, StudentFinancerInfo, StudentDocument, StudentAddress, StudentUser
from students.serializers import StudentOnboardingStepSerializer, StudentEducationSerializer, \
    StudentJobExperienceSerializer, StudentPassportSerializer, StudentForeignUniversitySerializer, \
    StudentFinancialInfoSerializer, StudentFinancerInfoSerializer, StudentDocumentSerializer, \
    StudentDocumentUploadSerializer, StudentAddressSerializer, StudentCompleteProfileSerializer, StudentUserSerializer
from students.utility.document_helper import google_bucket_file_upload, build_file_name, google_bucket_file_delete
from student_portal.permissions import IsStudent, IsBankAdmin, IsStudentAdmin, IsPriyoPay, IsAnyAdmin, is_any_admin

logger = logging.getLogger(__name__)
User = get_user_model()


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
                target_user = StudentUser.objects.filter(id=user_id).first()
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
                target_user = StudentUser.objects.filter(id=user_id).first()
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
    queryset = StudentUser.objects.all()
    ordering = ['-created_at']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return self.queryset.none()

        token_type = getattr(self.request.user, 'token_type', None)

        # Admin can see all records
        if token_type in ['local_admin', 'bank_admin']:
            return self.queryset.all()

        # Student can only see their own records
        return self.queryset.filter(id=self.request.user.id)


class EducationsViewSet(ModelViewSet):
    """GET/POST/PATCH /educations/"""
    http_method_names = ['get', 'post', 'patch']
    permission_classes = [IsStudent | IsAnyAdmin]  # ✅ OR logic
    authentication_classes = [JWTAuth]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    queryset = StudentEducation.objects.all()
    serializer_class = StudentEducationSerializer
    filterset_class = UserEducationFilterSet
    search_fields = ['institution_name', 'degree', 'field_of_study']
    ordering = ['-created_at']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return self.queryset.none()

        token_type = getattr(self.request.user, 'token_type', None)
        user_id = self.request.query_params.get('user')  # Admin can filter by user

        if token_type in ['local_admin', 'bank_admin']:  # ✅ Fix: changed from 'admin' to 'local_admin'
            if user_id:
                return self.queryset.filter(user_id=user_id)
            return self.queryset.all()

        return self.queryset.filter(user=self.request.user)


# Experience APIs - matches old backend /experiences/
class ExperiencesViewSet(ModelViewSet):  # 
    """GET/POST/PATCH /experiences/"""
    http_method_names = ['get', 'post', 'patch']
    permission_classes = [IsStudent | IsAnyAdmin]  # ✅ OR logic
    authentication_classes = [JWTAuth]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    queryset = StudentJobExperience.objects.all()
    serializer_class = StudentJobExperienceSerializer
    filterset_class = UserExperienceFilterSet
    search_fields = ['company_name', 'position']
    ordering = ['-created_at']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return self.queryset.none()

        token_type = getattr(self.request.user, 'token_type', None)

        # Admin can see all
        if token_type in ['local_admin', 'bank_admin']:
            return self.queryset.all()

        # Students see only their own
        return self.queryset.filter(user=self.request.user)


class StudentFirstStepViewSet(BaseStudentViewSet):
    """GET/POST/PATCH /student-first-step/ - Passport information"""
    http_method_names = ['get', 'post', 'patch']
    queryset = StudentPassport.objects.all()
    serializer_class = StudentPassportSerializer
    filterset_class = StudentPrimaryInfoFilterSet

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return self.queryset.none()

        if is_any_admin(self.request):
            return self.queryset.all()

        return self.queryset.filter(user=self.request.user)


class ForeignUniversitiesViewSet(BaseStudentViewSet):
    """GET/POST/PATCH /foreign-universities/"""
    http_method_names = ['get', 'post', 'patch']
    queryset = StudentForeignUniversity.objects.all()
    serializer_class = StudentForeignUniversitySerializer
    filterset_class = UserForeignUniversityFilterSet
    search_fields = ['university_name', 'country', 'program_name']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return self.queryset.none()

        if is_any_admin(self.request):
            return self.queryset.all()

        return self.queryset.filter(user=self.request.user)


class FinancialInfoViewSet(ModelViewSet):
    """GET/POST/PATCH /financial-info/"""
    http_method_names = ['get', 'post', 'patch']
    permission_classes = [IsStudent | IsAnyAdmin]
    authentication_classes = [JWTAuth]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    queryset = StudentFinancialInfo.objects.all()
    serializer_class = StudentFinancialInfoSerializer
    filterset_class = UserFinancialInfoFilterSet
    ordering = ['-created_at']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return self.queryset.none()

        if is_any_admin(self.request):
            return self.queryset.all()

        return self.queryset.filter(user=self.request.user)


class FinancerInfoViewSet(ModelViewSet):
    """GET/POST/PATCH /financer-info/"""
    http_method_names = ['get', 'post', 'patch']
    permission_classes = [IsStudent | IsAnyAdmin]
    authentication_classes = [JWTAuth]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    queryset = StudentFinancerInfo.objects.all()
    serializer_class = StudentFinancerInfoSerializer
    filterset_class = UserFinancerInfoFilterSet
    search_fields = ['financer_name', 'relationship']
    ordering = ['-created_at']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return self.queryset.none()

        if is_any_admin(self.request):
            return self.queryset.all()

        return self.queryset.filter(user=self.request.user)


class StudentDocumentsViewSet(BaseStudentViewSet):
    """GET/POST/PATCH /student-documents/ - matches old backend"""
    http_method_names = ['get', 'post', 'patch']
    queryset = StudentDocument.objects.all()
    serializer_class = StudentDocumentSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return self.queryset.none()

        if is_any_admin(self.request):
            return self.queryset.all()

        return self.queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return StudentDocumentUploadSerializer
        return StudentDocumentSerializer

    def create(self, request, *args, **kwargs):
        """Upload student documents - same logic as old backend"""
        serializer = StudentDocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        response_data, error_msg = self.upload_student_documents(
            serializer.validated_data,
            request.user
        )

        if error_msg:
            return Response({'Error': error_msg}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            data=StudentDocumentSerializer(response_data, many=True).data,
            status=status.HTTP_200_OK
        )

    def update(self, request, *args, **kwargs):
        """PATCH /student-documents/{id}/ - Update specific document"""
        instance = self.get_object()

        # Check if this is a file upload
        file_fields = [
            'student_photograph', 'financer_photograph', 'student_signature',
            'financer_signature', 'admission_letter', 'educational_certificate',
            'educational_transcript', 'university_invoice', 'financial_estimate',
            'language_test_result', 'other_documents'
        ]

        has_file_upload = any(field in request.data for field in file_fields)

        if has_file_upload:
            # Handle file upload for this specific document
            uploaded_file = None
            new_doc_type = None

            for field in file_fields:
                if field in request.data:
                    uploaded_file = request.data[field]
                    new_doc_type = field
                    break

            if uploaded_file:
                # Build bucket path - same as old backend
                bucket_folder_name = f"STUDENT/u{request.user.id}/{new_doc_type}"
                file_name = build_file_name(uploaded_file, bucket_folder_name)

                # Upload new file to GCP
                gcp_file_path, error_msg = google_bucket_file_upload(uploaded_file, file_name)

                if error_msg:
                    return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)

                if gcp_file_path:
                    # Delete old file from GCP if it exists
                    if instance.uploaded_file_name:
                        google_bucket_file_delete(instance.uploaded_file_name)

                    # Update the existing document record
                    instance.document_type = new_doc_type
                    instance.original_filename = uploaded_file.name
                    instance.uploaded_file_name = gcp_file_path
                    instance.file_size = uploaded_file.size
                    instance.save()
                else:
                    return Response({'error': 'Failed to upload file'}, status=status.HTTP_400_BAD_REQUEST)

        # Handle metadata updates (description, verification_status, etc.)
        serializer = StudentDocumentSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """PATCH /student-documents/{id}/ - Same as update for partial updates"""
        return self.update(request, *args, **kwargs)

    @classmethod
    def upload_student_documents(cls, validated_data, user):
        """Upload logic for CREATE - adapted from old backend"""
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

                    bucket_folder_name = f"STUDENT/u{user.id}/{doc_type}"
                    file_name = build_file_name(uploaded_file, bucket_folder_name)

                    # Upload to GCP
                    gcp_file_path, error_msg = google_bucket_file_upload(uploaded_file, file_name)

                    if gcp_file_path:
                        # Use update_or_create to handle existing documents
                        document, created = StudentDocument.objects.update_or_create(
                            user=user,
                            document_type=doc_type,
                            defaults={
                                'original_filename': uploaded_file.name,
                                'uploaded_file_name': gcp_file_path,
                                'file_size': uploaded_file.size,
                                'doc_type': 'STUDENT_DOCUMENTS',
                                'related_resource_type': 'student'
                            }
                        )

                        # If updating existing document, delete old file
                        if not created and document.uploaded_file_name != gcp_file_path:
                            # The old file path would be stored before update_or_create
                            pass  # Already handled by update_or_create

                        response_data.append(document)
                    else:
                        error_message = f"Failed to upload {doc_type}: {error_msg}"
                        break

            if len(response_data) == 0 and not error_message:
                error_message = "No files provided for upload!"

        except Exception as ex:
            error_message = str(ex)

        if len(response_data) > 0:
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


class StudentUsersViewSet(ModelViewSet):
    """GET /student-users/ - Student list for admin - matches old backend StudentUserViewSet"""
    http_method_names = ['get']
    permission_classes = [IsBankAdmin | IsStudentAdmin]
    authentication_classes = [JWTAuth]
    serializer_class = StudentUserSerializer
    search_fields = ['student_user__first_name', 'student_user__last_name', 'student_user__email']
    filterset_class = StudentUsersFilterSet
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering = ['-date_joined']

    def get_queryset(self):
        """Get users who have student_user records - matches old backend logic"""
        if getattr(self, 'swagger_fake_view', False):
            return StudentUser.objects.none()

        return StudentUser.objects.all()

    def get_serializer_context(self):
        """Add profile image context like old backend"""
        context = super().get_serializer_context()
        context['include_profile_image_icon'] = True  # Admin can see profile images
        return context


class UserViewSet(ModelViewSet):  # Don't inherit from BaseStudentViewSet
    """
    GET /user/ - Current user's own profile (Student access only) 
    GET /user/{id}/ - Complete student profile for admin
    """
    http_method_names = ['get', 'patch']
    authentication_classes = [JWTAuth]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    queryset = StudentUser.objects.all()
    ordering = ['-date_joined']  # User model has date_joined, not created_at

    def get_permissions(self):
        if self.action == 'list':
            permission_classes = [IsStudent]
        elif self.action == 'partial_update':
            permission_classes = [IsStudent | IsAnyAdmin]
        else:
            permission_classes = [IsAnyAdmin]

        return [permission() for permission in permission_classes]

    def get_authenticators(self):
        """Skip authentication for PriyoPay requests"""
        try:
            if hasattr(self.request, 'user') and IsPriyoPay().has_permission(self.request, self):
                return []
        except:
            pass
        return super().get_authenticators()

    def get_queryset(self):
        """Get all users - admin can access any user"""
        if getattr(self, 'swagger_fake_view', False):
            return StudentUser.objects.none()
        if is_any_admin(self.request):
            return StudentUser.objects.all()
        return StudentUser.objects.filter(id=self.request.user.id)

    def get_serializer_class(self):
        """Return complete profile serializer"""
        return StudentCompleteProfileSerializer

    def list(self, request, *args, **kwargs):
        """GET /user/ - Get current user's own profile (Student only)"""
        user = request.user
        serializer = StudentCompleteProfileSerializer(user, context={'request': request})
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """GET /user/{id}/ - Get specific user profile (Admin/PriyoPay only)"""
        user = self.get_object()
        serializer = StudentCompleteProfileSerializer(user, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['patch'])
    def update_by_uuid(self, request, *args, **kwargs):
        user = self.get_object()
        uuid = request.data.get('one_auth_uuid')
        if not uuid:
            return Response({'error': 'one_auth_uuid parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            student_user = StudentUser.objects.get(one_auth_uuid=uuid)
        except StudentUser.DoesNotExist:
            # Create minimal StudentUser if doesn't exist
            student_user: StudentUser = StudentUser.objects.create(
                one_auth_uuid=uuid,
                first_name=request.data.get('first_name') or 'FName',
                last_name=request.data.get('last_name') or 'LName',
                email=request.data.get('email_address') or f'student_{user.id}@temp.com',
            )

        try:
            priyopay_id = request.data.get('priyopay_id', None)
            mobile_number = request.data.get('mobile_number', None)
            date_of_birth = request.data.get('date_of_birth', None)
            gender = request.data.get('gender', None)
            nationality = request.data.get('nationality', None)

            if priyopay_id:
                student_user.priyopay_id = priyopay_id

            if mobile_number:
                student_user.mobile_number = mobile_number

            if date_of_birth:
                student_user.date_of_birth = date_of_birth

            if gender:
                student_user.gender = gender

            if nationality:
                student_user.nationality = nationality
            student_user.save()
        except Exception as ex:
            logger.error(ex)

        serializer = StudentCompleteProfileSerializer(student_user, context={'request': request})
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """PATCH /user/{id}/ - Update student profile (Admin/PriyoPay only)"""
        user = self.get_object()

        # try:
        #     student_user = user.student_user
        # except:
        #     return Response({'error': 'Student profile not found'}, status=404)

        serializer = StudentCompleteProfileSerializer(
            user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


# Address Management for Admin
class UserAddressViewSet(ModelViewSet):
    """GET/POST/PATCH /user-address/ - Address management"""
    http_method_names = ['get', 'post', 'patch']
    permission_classes = [IsStudent | IsAnyAdmin]  # Default for all actions
    authentication_classes = [JWTAuth]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    queryset = StudentAddress.objects.all()
    serializer_class = StudentAddressSerializer
    filterset_fields = ['address_type', 'user']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return self.queryset.none()

        if is_any_admin(self.request):
            return self.queryset.all()

        return self.queryset.filter(user=self.request.user)
