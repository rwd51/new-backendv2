from django.db import models

from utilities.model_mixins import TimeStampMixin


class BDBank(TimeStampMixin):
    bank_code = models.CharField(max_length=3, unique=True)
    bank_name = models.CharField(max_length=128, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.bank_name} ({self.bank_code})"
