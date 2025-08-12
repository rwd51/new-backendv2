from api_clients.priyopay_client import PriyoPayClient
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from student_portal.permissions import IsStudentAdmin, IsBankAdmin
from students.serializers import DepositClaimApproveSerializer, ConversionApproveSerializer


class DepositClaimsView(GenericAPIView):
    http_method_names = ['get', 'patch']
    permission_classes = [IsBankAdmin | IsStudentAdmin]


    def get(self, request, *args, **kwargs):
        response, _ = PriyoPayClient().fetch_deposit_claims()
        return Response(response, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        serializer = DepositClaimApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        response, _ = PriyoPayClient().update_deposit_claims(
            claim_id=request.data['claim_id'],
            payload={
                'claim_status': 'APPROVED',
            }
        )
        return Response(response, status=status.HTTP_200_OK)


class BDTtoUSDView(GenericAPIView):
    http_method_names = ['get', 'patch']
    permission_classes = [IsBankAdmin | IsStudentAdmin]

    def get(self, request, *args, **kwargs):
        response, _ = PriyoPayClient().fetch_conversions()
        return Response(response, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        serializer = ConversionApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        response, _ = PriyoPayClient().update_conversion(
            conversion_id=request.data['conversion_id'],
            payload={
                'request_status': 'APPROVED',
            }
        )
        return Response(response, status=status.HTTP_200_OK)