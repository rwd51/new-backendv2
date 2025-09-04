from django.conf import settings
from rest_framework.serializers import ModelSerializer
from student_admin.models import BDBank


class BdBankSerializer(ModelSerializer):
    class Meta:
        model = BDBank
        fields = '__all__'
