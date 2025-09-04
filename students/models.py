from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from students.enums import StudentOnboardingSteps, ServiceList
from utilities.model_mixins import TimeStampMixin


class CustomUser(AbstractUser):
    admin_type = models.CharField(max_length=50, null=True, blank=True, choices=[
        ('bank_admin', 'Bank Admin'),
        ('student_admin', 'Student Admin')
    ])
    department = models.CharField(max_length=100, null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField()

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.admin_type})"


# Main Student Model - matches priyo_pay_backend StudentUser
class StudentUser(TimeStampMixin):
    """Main student model - matches priyo_pay_backend StudentUser"""
    # user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_user")
    one_auth_uuid = models.UUIDField(unique=True, null=True, blank=True)
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
    is_active = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(CustomUser, on_delete=models.PROTECT, null=True, blank=True, related_name='approved_students')
    approved_at = models.DateTimeField(null=True, blank=True)
    last_login = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(default=timezone.now)


class StudentAddress(TimeStampMixin):
    """Student address - matches priyo_pay_backend pattern"""
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_addresses')
    user = models.ForeignKey(StudentUser, on_delete=models.CASCADE, related_name='student_addresses', default=None)
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


class StudentEducation(TimeStampMixin):
    """Student education records - matches priyo_pay_backend naming"""
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_educations')
    user = models.ForeignKey(StudentUser, on_delete=models.CASCADE, related_name='student_educations', default=None)
    institution_name = models.CharField(max_length=200)
    degree = models.CharField(max_length=100)
    field_of_study = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    grade = models.CharField(max_length=10, null=True, blank=True)
    is_current = models.BooleanField(default=False)


class StudentJobExperience(TimeStampMixin):
    """Student job experience - matches priyo_pay_backend naming"""
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_job_experiences')  # Fixed
    user = models.ForeignKey(StudentUser, on_delete=models.CASCADE, related_name='student_job_experiences',
                             default=None)
    company_name = models.CharField(max_length=200)
    position = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    is_current = models.BooleanField(default=False)


class StudentForeignUniversity(TimeStampMixin):
    """Student foreign university information - matches priyo_pay_backend naming"""
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_foreign_universities')
    user = models.ForeignKey(StudentUser, on_delete=models.CASCADE, related_name='student_foreign_universities',
                             default=None)
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


class StudentFinancialInfo(TimeStampMixin):
    """Student financial information - matches priyo_pay_backend naming"""
    # user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_financial_info')
    user = models.OneToOneField(StudentUser, on_delete=models.CASCADE, related_name='student_financial_info',
                                default=None)

    # Existing fields (keep as is)
    annual_family_income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    savings_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    loan_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    other_funding_sources = models.TextField(blank=True)
    bank_statement_available = models.BooleanField(default=False)

    # ADD THESE MISSING FIELDS for frontend compatibility:
    foreign_currency_purchase_date = models.DateField(blank=True, null=True)
    purchased_currency_amount_in_cent = models.IntegerField(default=0, blank=True, null=True)
    scholarship_title = models.CharField(max_length=255, blank=True, null=True)
    scholarship_amount_in_cent = models.IntegerField(default=0, blank=True, null=True)
    scholarship_period = models.CharField(max_length=255, blank=True, null=True)
    estimated_income_in_cent_from_part_time_per_month = models.IntegerField(default=0, blank=True, null=True)
    remittance_by_other_channels = models.TextField(blank=True, null=True)
    willing_to_return_to_bd = models.BooleanField(default=False)

    # New field for Student File Bank Name
    student_file_bank_name = models.CharField(max_length=255, blank=True, null=True)


class StudentFinancerInfo(TimeStampMixin):
    """Student financer information - matches priyo_pay_backend naming"""
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_financer_info')
    user = models.ForeignKey(StudentUser, on_delete=models.CASCADE, related_name='student_financer_info', default=None)
    financer_name = models.CharField(max_length=200)
    relationship = models.CharField(max_length=100)
    occupation = models.CharField(max_length=200)
    monthly_income_usd = models.DecimalField(max_digits=12, decimal_places=2)
    yearly_income_usd = models.DecimalField(max_digits=12, decimal_places=2)
    contact_number = models.CharField(max_length=20)
    email = models.EmailField()
    is_primary_financer = models.BooleanField(default=False)


class StudentPassport(TimeStampMixin):
    # user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_passport')
    user = models.OneToOneField(StudentUser, on_delete=models.CASCADE, related_name='student_passport', default=None)
    passport_number = models.CharField(max_length=50)
    passport_issue_place = models.CharField(max_length=100)  # ✅ ADD THIS
    passport_issue_date = models.DateField()
    passport_expiry_date = models.DateField()


class StudentOnboardingStep(TimeStampMixin):
    """Student onboarding progress tracking - matches priyo_pay_backend pattern"""
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_onboarding_steps')
    user = models.ForeignKey(StudentUser, on_delete=models.CASCADE, related_name='student_onboarding_steps',
                             default=None)
    step = models.CharField(max_length=50, choices=StudentOnboardingSteps.choices())
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    step_data = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ('user', 'step')


# Add these document types to your existing StudentDocument model
class StudentDocument(TimeStampMixin):
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

    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_documents')
    user = models.ForeignKey(StudentUser, on_delete=models.CASCADE, related_name='student_documents', default=None)
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


class ServiceKey(models.Model):
    secret_key = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    service = models.CharField(max_length=15, choices=ServiceList.choices())

    class Meta:
        db_table = 'students_service_key'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['secret_key']),
            models.Index(fields=['service']),
        ]

    def __str__(self):
        return str(self.pk)

    @classmethod
    def get_service_from_api_key(cls, api_key):
        if not cls.objects.filter(secret_key=api_key).exists():
            return None, None
        service_key = cls.objects.filter(secret_key=api_key).first()
        return service_key.service

    @classmethod
    def get_key_from_service(cls, service):
        if not cls.objects.filter(service=service).exists():
            return None
        return cls.objects.filter(service=service).first().secret_key
