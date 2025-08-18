from api_clients.priyopay_client import PriyoPayClient
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from student_portal.permissions import IsStudentAdmin, IsBankAdmin
from students.serializers import DepositClaimApproveSerializer, ConversionApproveSerializer, ConversionCreateSerializer


class DepositClaimsView(GenericAPIView):
    http_method_names = ['get', 'patch']
    permission_classes = [IsBankAdmin | IsStudentAdmin]

    def get(self, request, pk=None, *args, **kwargs):
        response, _ = PriyoPayClient().fetch_deposit_claims()
        
        # If pk is provided, return specific deposit
        if pk:
            if response and 'results' in response:
                for deposit in response['results']:
                    if str(deposit.get('id')) == str(pk) or str(deposit.get('claim_id')) == str(pk):
                        return Response(deposit, status=status.HTTP_200_OK)
            return Response({'error': 'Deposit not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Otherwise return all deposits
        return Response(response, status=status.HTTP_200_OK)

    def patch(self, request, pk=None, *args, **kwargs):
        claim_id = pk or request.data.get('claim_id')
        if not claim_id:
            return Response({'error': 'claim_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        serializer = DepositClaimApproveSerializer(data={'claim_id': claim_id})
        serializer.is_valid(raise_exception=True)

        response, _ = PriyoPayClient().update_deposit_claims(
            claim_id=claim_id,
            payload={'claim_status': 'APPROVED'}
        )
        return Response(response, status=status.HTTP_200_OK)


class BDTtoUSDView(GenericAPIView):
    http_method_names = ['get', 'post', 'patch']
    permission_classes = [IsBankAdmin | IsStudentAdmin]

    def get(self, request, pk=None, *args, **kwargs):
        response, _ = PriyoPayClient().fetch_conversions()
        
        # If pk is provided, return specific conversion
        if pk:
            if response and 'results' in response:
                for conversion in response['results']:
                    if str(conversion.get('id')) == str(pk) or str(conversion.get('conversion_id')) == str(pk):
                        return Response(conversion, status=status.HTTP_200_OK)
            return Response({'error': 'Conversion not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Otherwise return all conversions
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        # Create new conversion request - send raw data without validation
        response, status_code = PriyoPayClient().create_conversion(payload=request.data)
        return Response(response, status=status_code)

    def patch(self, request, pk=None, *args, **kwargs):
        conversion_id = pk or request.data.get('conversion_id')
        if not conversion_id:
            return Response({'error': 'conversion_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        serializer = ConversionApproveSerializer(data={'conversion_id': conversion_id})
        serializer.is_valid(raise_exception=True)

        response, _ = PriyoPayClient().update_conversion(
            conversion_id=conversion_id,
            payload={'request_status': 'APPROVED'}
        )
        return Response(response, status=status.HTTP_200_OK)


class USDAccountsView(GenericAPIView):
    http_method_names = ['get']
    permission_classes = [IsStudentAdmin | IsBankAdmin]

    def get(self, request, user_id=None, *args, **kwargs):
        # Mock USD account data
        mock_data = {
            "count": 1,
            "next": None,
            "previous": None,
            "start_index": 0,
            "end_index": 0,
            "results": [
                {
                    "id": 991,
                    "creator": {
                        "id": 2109,
                        "first_name": "John",
                        "middle_name": "",
                        "last_name": "Smith",
                        "email_address": "johnsmith123@yopmail.com"
                    },
                    "account_details": {
                        "id": 520,
                        "profile_type": "PERSON",
                        "synctera_account_balance": 225.0,
                        "synctera_available_balance": 225.0,
                        "pending_amount": 0.0,
                        "updated_at": "2025-08-16T01:09:39.022626-07:00",
                        "account": 991,
                        "hold_balance": 0.0
                    },
                    "account_holder_name": "John Smith",
                    "created_at": "2025-08-13T10:19:02.565889-07:00",
                    "updated_at": "2025-08-16T01:09:39.017831-07:00",
                    "account_number": "101056480334541",
                    "account_type": "CHECKING",
                    "account_process_type": "USER",
                    "account_status": "ACTIVE_OR_DISBURSED",
                    "nickname": "My USD Account",
                    "synctera_account_id": "415b9d11-d713-42b3-9d8c-6eedcac395a8",
                    "data": {
                        "id": "415b9d11-d713-42b3-9d8c-6eedcac395a8",
                        "status": "ACTIVE_OR_DISBURSED",
                        "tenant": "pnrqep_yvkkwp",
                        "balances": [
                            {
                                "type": "ACCOUNT_BALANCE",
                                "balance": 0
                            },
                            {
                                "type": "AVAILABLE_BALANCE",
                                "balance": 0
                            }
                        ],
                        "currency": "USD",
                        "nickname": "My USD Account",
                        "open_date": "2025-08-13",
                        "is_security": False,
                        "account_type": "CHECKING",
                        "bank_routing": "359867415",
                        "customer_ids": [
                            "bbe79085-fbdd-4701-8a20-1fe78945b6e1"
                        ],
                        "restrictions": {
                            "is_account_out_of_area": True
                        },
                        "access_status": "ACTIVE",
                        "creation_time": "2025-08-13T17:19:02.302773Z",
                        "customer_type": "PERSONAL",
                        "account_number": "101056480334541",
                        "is_ach_enabled": True,
                        "is_p2p_enabled": True,
                        "is_sar_enabled": False,
                        "bank_account_id": "be190a59-a6ee-4080-aa13-f697c9ab6955",
                        "is_account_pool": False,
                        "is_card_enabled": True,
                        "is_wire_enabled": True,
                        "is_eft_ca_enabled": False,
                        "last_updated_time": "2025-08-13T17:19:02.302773Z",
                        "account_template_id": "c3e41f0a-53b0-4901-9a47-dc252ca8fcb6",
                        "account_number_masked": "101056*****4541",
                        "is_synctera_pay_enabled": True,
                        "is_external_card_enabled": False,
                        "access_status_last_updated_time": "2025-08-13T17:19:02.332675Z"
                    },
                    "profile": 1541
                }
            ]
        }
        
        return Response(mock_data, status=status.HTTP_200_OK)