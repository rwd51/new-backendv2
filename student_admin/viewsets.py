from student_admin.models import BDBank
from student_admin.serializers import BdBankSerializer
from rest_framework.viewsets import ModelViewSet
from student_portal.authentication import JWTAuth
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle
from student_portal.permissions import IsStudent, IsBankAdmin, IsStudentAdmin


class PublicListAnonThrottle(AnonRateThrottle):
    scope = 'public_bd_bank_list'


class BdBankViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch']
    authentication_classes = [JWTAuth]
    permission_classes = [IsStudent | IsBankAdmin | IsStudentAdmin]

    queryset = BDBank.objects.all()
    serializer_class = BdBankSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return BDBank.objects.none()
        return BDBank.objects.filter(is_active=True).order_by('bank_name')

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsStudentAdmin()]
        elif self.action == 'list':
            return [AllowAny()]
        return super().get_permissions()

    def get_throttles(self):
        if self.action == 'list':
            return [PublicListAnonThrottle()]
        return super().get_throttles()
