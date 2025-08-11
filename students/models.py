from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from students.enums import StudentOnboardingSteps
import uuid
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class CustomUser(AbstractUser):
    """Minimal user model - bridge to external auth service"""
    one_auth_uuid = models.UUIDField(unique=True, null=True, blank=True)
    admin_type = models.CharField(max_length=50, null=True, blank=True)
    
    # Remove first_name, last_name from here since StudentUser has them
    
    def __str__(self):
        if hasattr(self, 'student_user'):
            return f"{self.student_user.first_name} {self.student_user.last_name}"
        return self.username or str(self.one_auth_uuid)


class BaseModel(models.Model):
    """Base model with common fields"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class AdminUser(BaseModel):
    """Separate admin user model - cleaner separation"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="admin_user")
    
    # Admin specific fields
    admin_type = models.CharField(max_length=50, choices=[
        ('bank_admin', 'Bank Admin'),
        ('student_admin', 'Student Admin')
    ])
    department = models.CharField(max_length=100, null=True, blank=True)
    permissions = models.JSONField(default=dict, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Basic info (since auth service might not provide)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.admin_type})"

# Main Student Model - matches priyo_pay_backend StudentUser
class StudentUser(BaseModel):
    """Main student model - matches priyo_pay_backend StudentUser"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_user")
    
    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    mobile_number = models.CharField(max_length=20, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    nationality = models.CharField(max_length=100, null=True, blank=True)
    priyopay_id = models.IntegerField(null=True, blank=True)

    # Status fields
    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='approved_students')
    approved_at = models.DateTimeField(null=True, blank=True)
    


class StudentAddress(BaseModel):
    """Student address - matches priyo_pay_backend pattern"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_addresses')
    address_type = models.CharField(max_length=20, choices=[
        ('permanent', 'Permanent'),
        ('current', 'Current'),
        ('mailing', 'Mailing')
    ])
    street_address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

class StudentEducation(BaseModel):
    """Student education records - matches priyo_pay_backend naming"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_educations') 
    institution_name = models.CharField(max_length=200)
    degree = models.CharField(max_length=100)
    field_of_study = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    grade = models.CharField(max_length=10, null=True, blank=True)
    is_current = models.BooleanField(default=False)

class StudentJobExperience(BaseModel):
    """Student job experience - matches priyo_pay_backend naming"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_job_experiences')  # Fixed
    company_name = models.CharField(max_length=200)
    position = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    is_current = models.BooleanField(default=False)

class StudentForeignUniversity(BaseModel):
    """Student foreign university information - matches priyo_pay_backend naming"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_foreign_universities')
    university_name = models.CharField(max_length=200)
    country = models.CharField(max_length=100)
    program_name = models.CharField(max_length=200)
    degree_level = models.CharField(max_length=50)
    duration_years = models.IntegerField()
    tuition_fee_usd = models.DecimalField(max_digits=12, decimal_places=2)
    living_cost_usd = models.DecimalField(max_digits=12, decimal_places=2)
    total_cost_usd = models.DecimalField(max_digits=12, decimal_places=2)
    application_deadline = models.DateField()
    program_start_date = models.DateField()

class StudentFinancialInfo(BaseModel):
    """Student financial information - matches priyo_pay_backend naming"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_financial_info') 
    monthly_income_usd = models.DecimalField(max_digits=12, decimal_places=2)
    yearly_income_usd = models.DecimalField(max_digits=12, decimal_places=2)
    savings_usd = models.DecimalField(max_digits=12, decimal_places=2)
    family_contribution_usd = models.DecimalField(max_digits=12, decimal_places=2)
    loan_required_usd = models.DecimalField(max_digits=12, decimal_places=2)
    bank_statement_available = models.BooleanField(default=False)

class StudentFinancerInfo(BaseModel):
    """Student financer information - matches priyo_pay_backend naming"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_financer_info')
    financer_name = models.CharField(max_length=200)
    relationship = models.CharField(max_length=100)
    occupation = models.CharField(max_length=200)
    monthly_income_usd = models.DecimalField(max_digits=12, decimal_places=2)
    yearly_income_usd = models.DecimalField(max_digits=12, decimal_places=2)
    contact_number = models.CharField(max_length=20)
    email = models.EmailField()
    is_primary_financer = models.BooleanField(default=False)

class StudentPassport(BaseModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_passport')
    passport_number = models.CharField(max_length=50)
    passport_issue_place = models.CharField(max_length=100)  # ✅ ADD THIS
    passport_issue_date = models.DateField() 
    passport_expiry_date = models.DateField()  

class StudentOnboardingStep(BaseModel):
    """Student onboarding progress tracking - matches priyo_pay_backend pattern"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_onboarding_steps') 
    step = models.CharField(max_length=50, choices=StudentOnboardingSteps.choices())
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    step_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        unique_together = ('user', 'step')

# Add these document types to your existing StudentDocument model
class StudentDocument(BaseModel):
    """Student documents/files - matches priyo_pay_backend Documents model"""
    DOCUMENT_TYPES = [
        ('student_photograph', 'Student Photograph'),
        ('financer_photograph', 'Financer Photograph'), 
        ('student_signature', 'Student Signature'),
        ('financer_signature', 'Financer Signature'),
        ('admission_letter', 'Admission Letter'),
        ('educational_certificate', 'Educational Certificate'),
        ('educational_transcript', 'Educational Transcript'),
        ('university_invoice', 'University Invoice'),
        ('financial_estimate', 'Financial Estimate'),
        ('language_test_result', 'Language Test Result'),
        ('other_documents', 'Other Documents'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    original_filename = models.CharField(max_length=255)
    uploaded_file_name = models.CharField(max_length=256)  # GCP path
    gcp_url = models.URLField(max_length=500, null=True, blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    
    # Match old backend fields
    doc_type = models.CharField(max_length=32, default='STUDENT_DOCUMENTS')
    related_resource_type = models.CharField(max_length=50, default='student')
    verification_status = models.CharField(max_length=16, default='UNVERIFIED')

    class Meta:
        ordering = ('-updated_at',)