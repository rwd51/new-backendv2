from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import *
from .validators import FileValidator

User = get_user_model()

class StudentUserAutoCreateMixin:
    """Mixin to auto-create StudentUser AND update onboarding progress"""
    def get_or_create_student_user(self, user):
        student_user, created = StudentUser.objects.get_or_create(
            user=user,
            defaults={
                'first_name': 'Student',
                'last_name': f'#{user.id}',
                'email': f'student_{user.id}@temp.com',
            }
        )
        return student_user
    
    def update_onboarding_progress(self, user, step_name):
        """Auto-update onboarding step when data is saved"""
        from django.utils import timezone
        StudentOnboardingStep.objects.update_or_create(
            user=user,
            step=step_name,
            defaults={
                'is_completed': True,
                'completed_at': timezone.now(),
                'step_data': {'auto_completed': True}
            }
        )

    def create(self, validated_data):
        user = self.context['request'].user
        self.get_or_create_student_user(user)
        validated_data['user'] = user
        
        # Auto-update onboarding progress
        step_mapping = {
            'StudentEducationSerializer': 'student_education',
            'StudentJobExperienceSerializer': 'student_experience', 
            'StudentPassportSerializer': 'student_primary_info',
            'StudentForeignUniversitySerializer': 'student_foreign_university',
            'StudentFinancialInfoSerializer': 'student_financial_info',
            'StudentFinancerInfoSerializer': 'student_financer_info',
        }
        
        step_name = step_mapping.get(self.__class__.__name__)
        if step_name:
            self.update_onboarding_progress(user, step_name)
        
        return super().create(validated_data)

class StudentEducationSerializer(StudentUserAutoCreateMixin, serializers.ModelSerializer):
    class Meta:
        model = StudentEducation
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        user = self.context['request'].user
        self.get_or_create_student_user(user)  # Auto-create StudentUser
        validated_data['user'] = user
        return super().create(validated_data)

class StudentJobExperienceSerializer(StudentUserAutoCreateMixin, serializers.ModelSerializer):
    class Meta:
        model = StudentJobExperience
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        user = self.context['request'].user
        self.get_or_create_student_user(user)
        validated_data['user'] = user
        return super().create(validated_data)

class StudentPassportSerializer(StudentUserAutoCreateMixin, serializers.ModelSerializer):
    class Meta:
        model = StudentPassport
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        user = self.context['request'].user
        self.get_or_create_student_user(user)
        validated_data['user'] = user
        return super().create(validated_data)

class StudentForeignUniversitySerializer(StudentUserAutoCreateMixin, serializers.ModelSerializer):
    class Meta:
        model = StudentForeignUniversity
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        user = self.context['request'].user
        self.get_or_create_student_user(user)
        validated_data['user'] = user
        return super().create(validated_data)

class StudentFinancialInfoSerializer(StudentUserAutoCreateMixin, serializers.ModelSerializer):
    class Meta:
        model = StudentFinancialInfo
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        user = self.context['request'].user
        self.get_or_create_student_user(user)
        validated_data['user'] = user
        return super().create(validated_data)

class StudentFinancerInfoSerializer(StudentUserAutoCreateMixin, serializers.ModelSerializer):
    class Meta:
        model = StudentFinancerInfo
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        user = self.context['request'].user
        self.get_or_create_student_user(user)
        validated_data['user'] = user
        return super().create(validated_data)

# In students/serializers.py - Replace/Add these serializers

# In students/serializers.py - ONLY replace the StudentUserSerializer class
# Keep everything else unchanged

# In students/serializers.py - ONLY replace the StudentUserSerializer class
# Keep everything else unchanged
# In students/serializers.py - ONLY replace the StudentUserSerializer class
# Keep everything else unchanged

class StudentUserSerializer(serializers.ModelSerializer):
    """Matches old backend StudentUserSerializer response format"""
    
    # Add fields that match old backend PriyoMoneyUserSerializer
    university = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    foreign_university = serializers.SerializerMethodField()  # Added this
    profile_image_icon = serializers.SerializerMethodField()
    mobile_number = serializers.SerializerMethodField()
    last_onboarding_step = serializers.SerializerMethodField()
    
    # Basic user info from CustomUser model - FIXED: use proper sources
    id = serializers.IntegerField(source='student_user.id', read_only=True)
    first_name = serializers.CharField(source='student_user.first_name', read_only=True)
    last_name = serializers.CharField(source='student_user.last_name', read_only=True)
    email = serializers.CharField(source='student_user.email', read_only=True)
    date_of_birth = serializers.DateField(source='student_user.date_of_birth', read_only=True)
    gender = serializers.CharField(source='student_user.gender', read_only=True)
    nationality = serializers.CharField(source='student_user.nationality', read_only=True)
    is_active = serializers.BooleanField(source='student_user.is_active', read_only=True)
    is_approved = serializers.BooleanField(source='student_user.is_approved', read_only=True)
    
    one_auth_uuid = serializers.CharField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = User  # Changed to User model since that's what the viewset returns
        fields = [
            'id', 'one_auth_uuid', 'first_name', 'last_name', 'email', 
            'mobile_number', 'date_of_birth', 'gender', 'nationality',
            'is_active', 'is_approved', 
            'university', 'department', 'foreign_university', 'profile_image_icon', 
            'last_onboarding_step', 'date_joined'
        ]
    
    def get_university(self, obj):
        """Get latest university from educations - obj is User"""
        education = obj.student_educations.order_by('-created_at').first()
        return education.institution_name if education else None
    
    def get_department(self, obj):
        """Get latest department from educations - obj is User"""  
        education = obj.student_educations.order_by('-created_at').first()
        return education.field_of_study if education else None
    
    def get_foreign_university(self, obj):
        """Get foreign university info - obj is User"""
        foreign_uni = obj.student_foreign_universities.order_by('-created_at').first()
        if foreign_uni:
            return {
                'university_name': foreign_uni.university_name,
                'country': foreign_uni.country,
                'program_name': foreign_uni.program_name,
                'degree_level': foreign_uni.degree_level
            }
        return None
    
    def get_profile_image_icon(self, obj):
        """Get profile image if available - obj is User"""
        if not self.context.get('include_profile_image_icon'):
            return None
        
        # Look for student photograph in documents
        document = obj.student_documents.filter(
            document_type='student_photograph'
        ).first()
        
        if document and document.uploaded_file_name:
            from .utility.document_helper import google_bucket_file_url
            return google_bucket_file_url(document.uploaded_file_name)
        return None
    
    def get_mobile_number(self, obj):
        """Return mobile number info - obj is User"""
        try:
            student_user = obj.student_user
            if student_user.mobile_number:
                return {
                    'mobile_number': student_user.mobile_number,
                    'mobile_number_country_prefix': '+880'  # Default for BD
                }
        except:
            pass
        return None
    
    def get_last_onboarding_step(self, obj):
        """Get last completed onboarding step - obj is User"""
        finished_steps = obj.student_onboarding_steps.filter(
            is_completed=True
        ).values_list('step', flat=True)
        
        expected_steps = [
            'student_primary_info', 'student_education', 'student_experience',
            'student_foreign_university', 'student_financial_info', 
            'student_financer_info', 'student_documents_upload'
        ]
        
        for step in reversed(expected_steps):
            if step in finished_steps:
                return step
        return None

class StudentCompleteProfileSerializer(serializers.ModelSerializer):
    """Complete student profile - matches old backend PriyoMoneyUserSerializer format"""
    
    # Related data - matches old backend nested structure
    addresses = serializers.SerializerMethodField()
    educations = serializers.SerializerMethodField()  
    experiences = serializers.SerializerMethodField()
    universities = serializers.SerializerMethodField()
    financial_info = serializers.SerializerMethodField()
    financer_info = serializers.SerializerMethodField()
    passport = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    onboarding_progress = serializers.SerializerMethodField()
    
    # Basic fields from StudentUser
    university = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    profile_image_icon = serializers.SerializerMethodField()
    
    # User fields
    one_auth_uuid = serializers.CharField(source='user.one_auth_uuid', read_only=True)
    date_joined = serializers.DateTimeField(source='user.date_joined', read_only=True)
    
    class Meta:
        model = StudentUser
        fields = [
            # Basic info
            'id', 'user', 'one_auth_uuid', 'first_name', 'last_name', 'email',
            'mobile_number', 'date_of_birth', 'gender', 'nationality',
            'is_active', 'is_approved', 'approved_by', 'approved_at',
            'created_at', 'updated_at', 'date_joined',
            
            # Derived fields
            'university', 'department', 'profile_image_icon',
            
            # Related data
            'addresses', 'educations', 'experiences', 'universities',
            'financial_info', 'financer_info', 'passport', 'documents',
            'onboarding_progress'
        ]
    
    def get_addresses(self, obj):
        addresses = obj.user.student_addresses.all()
        return StudentAddressSerializer(addresses, many=True).data
    
    def get_educations(self, obj):
        educations = obj.user.student_educations.all()
        return StudentEducationSerializer(educations, many=True).data
    
    def get_experiences(self, obj):
        experiences = obj.user.student_job_experiences.all()
        return StudentJobExperienceSerializer(experiences, many=True).data
    
    def get_universities(self, obj):
        universities = obj.user.student_foreign_universities.all()
        return StudentForeignUniversitySerializer(universities, many=True).data
    
    def get_financial_info(self, obj):
        try:
            return StudentFinancialInfoSerializer(obj.user.student_financial_info).data
        except:
            return None
    
    def get_financer_info(self, obj):
        financer_info = obj.user.student_financer_info.all()
        return StudentFinancerInfoSerializer(financer_info, many=True).data
    
    def get_passport(self, obj):
        try:
            return StudentPassportSerializer(obj.user.student_passport).data
        except:
            return None
    
    def get_documents(self, obj):
        documents = obj.user.student_documents.all()
        return StudentDocumentSerializer(documents, many=True).data
    
    def get_university(self, obj):
        education = obj.user.student_educations.order_by('-created_at').first()
        return education.institution_name if education else None
    
    def get_department(self, obj):
        education = obj.user.student_educations.order_by('-created_at').first()
        return education.field_of_study if education else None
    
    def get_profile_image_icon(self, obj):
        document = obj.user.student_documents.filter(
            document_type='student_photograph'
        ).first()
        
        if document and document.uploaded_file_name:
            from .utility.document_helper import google_bucket_file_url
            return google_bucket_file_url(document.uploaded_file_name)
        return None
    
    def get_onboarding_progress(self, obj):
        """Get onboarding progress - matches old backend"""
        steps = obj.user.student_onboarding_steps.all()
        finished_steps = steps.values_list('step', flat=True)
        
        expected_steps = [
            'student_primary_info', 'student_education', 'student_experience',
            'student_foreign_university', 'student_financial_info', 
            'student_financer_info', 'student_documents_upload'
        ]
        
        progress = []
        for step in expected_steps:
            step_obj = steps.filter(step=step).first()
            progress.append({
                'step': step,
                'finished': step in finished_steps,
                'is_completed': step_obj.is_completed if step_obj else False,
                'completed_at': step_obj.completed_at if step_obj else None
            })
        
        completed_count = len([s for s in progress if s['is_completed']])
        
        return {
            'progress_percentage': (completed_count / len(expected_steps) * 100) if expected_steps else 0,
            'completed_steps': completed_count,
            'total_steps': len(expected_steps),
            'steps': progress
        }



class StudentDocumentSerializer(serializers.ModelSerializer):
    gcp_url = serializers.SerializerMethodField()  # ✅ CORRECT
    
    def get_gcp_url(self, obj):
        """Get GCP URL using same method as old backend"""
        if obj.uploaded_file_name:
            from .utility.document_helper import google_bucket_file_url
            return google_bucket_file_url(obj.uploaded_file_name)
        return None
    
    class Meta:
        model = StudentDocument
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at', 'uploaded_file_name', 'gcp_url')

class StudentDocumentUploadSerializer(serializers.Serializer):
    """Document upload - matches old backend pattern"""
    student_photograph = serializers.FileField(required=False, validators=[
        FileValidator(max_size=5*1024*1024, allowed_extensions=('pdf', 'jpg', 'png', 'jpeg'))
    ])
    financer_photograph = serializers.FileField(required=False, validators=[
        FileValidator(max_size=5*1024*1024, allowed_extensions=('pdf', 'jpg', 'png', 'jpeg'))
    ])
    student_signature = serializers.FileField(required=False, validators=[
        FileValidator(max_size=5*1024*1024, allowed_extensions=('pdf', 'jpg', 'png', 'jpeg'))
    ])
    financer_signature = serializers.FileField(required=False, validators=[
        FileValidator(max_size=5*1024*1024, allowed_extensions=('pdf', 'jpg', 'png', 'jpeg'))
    ])
    admission_letter = serializers.FileField(required=False, validators=[
        FileValidator(max_size=5*1024*1024, allowed_extensions=('pdf', 'jpg', 'png', 'jpeg'))
    ])
    educational_certificate = serializers.FileField(required=False, validators=[
        FileValidator(max_size=5*1024*1024, allowed_extensions=('pdf', 'jpg', 'png', 'jpeg'))
    ])
    educational_transcript = serializers.FileField(required=False, validators=[
        FileValidator(max_size=5*1024*1024, allowed_extensions=('pdf', 'jpg', 'png', 'jpeg'))
    ])
    university_invoice = serializers.FileField(required=False, validators=[
        FileValidator(max_size=5*1024*1024, allowed_extensions=('pdf', 'jpg', 'png', 'jpeg'))
    ])
    financial_estimate = serializers.FileField(required=False, validators=[
        FileValidator(max_size=5*1024*1024, allowed_extensions=('pdf', 'jpg', 'png', 'jpeg'))
    ])
    language_test_result = serializers.FileField(required=False, validators=[
        FileValidator(max_size=5*1024*1024, allowed_extensions=('pdf', 'jpg', 'png', 'jpeg'))
    ])
    other_documents = serializers.FileField(required=False, validators=[
        FileValidator(max_size=5*1024*1024, allowed_extensions=('pdf', 'jpg', 'png', 'jpeg'))
    ])
class StudentOnboardingStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentOnboardingStep
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')



class StudentAddressSerializer(StudentUserAutoCreateMixin, serializers.ModelSerializer):
    class Meta:
        model = StudentAddress
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')