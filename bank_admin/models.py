from django.db import models

from student_admin.models import BDBank
from utilities.model_mixins import TimeStampMixin


class BankAdminUser(TimeStampMixin):
    user_id = models.CharField(max_length=255, unique=True)  # Supabase user ID
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
    is_email_verified = models.BooleanField(default=False)

    is_approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True)

    bd_bank = models.ForeignKey(BDBank, on_delete=models.PROTECT, related_name='bank_admin_users', null=True)

    def __str__(self):
        return f"{self.email} ({self.first_name} {self.last_name})"
