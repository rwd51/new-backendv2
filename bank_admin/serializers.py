from rest_framework import serializers
from bank_admin.models import BankAdminUser
from student_admin.models import BDBank
from student_admin.serializers import BdBankSerializer


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    bd_bank = serializers.PrimaryKeyRelatedField(queryset=BDBank.objects.all(), write_only=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()


class SigninSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class BankAdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAdminUser
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['bd_bank'] = BdBankSerializer(instance.bd_bank).data
        if instance.approved_by:
            representation["approved_by"] = {
                "email": instance.approved_by.email,
                "first_name": instance.approved_by.first_name,
                "last_name": instance.approved_by.last_name,
            }
        return representation


class BankAdminApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAdminUser
        fields = ["is_approved"]
        read_only_fields = ("user_id", "email", "first_name", "last_name", "approved_at")
