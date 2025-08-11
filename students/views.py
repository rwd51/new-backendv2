from api_clients.priyopay_client import PriyoPayClient
from rest_framework.generics import GenericAPIView

from student_portal.permissions import IsStudentAdmin, IsBankAdmin


class DepositClaimsView(GenericAPIView):
    http_method_names = ['get', 'post']
    permission_classes = [IsBankAdmin | IsStudentAdmin]


    def get(self, request, *args, **kwargs):
        response, _ = PriyoPayClient().fetch_deposit_claims()
        return response

    def patch(self, request, *args, **kwargs):
        response, _ = PriyoPayClient().update_deposit_claims(
            claim_id=request.data['claim_id'],
            payload={
                'claim_status': 'APPROVED',
            }
        )
        return response