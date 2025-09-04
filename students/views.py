from api_clients.priyopay_client import PriyoPayClient
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from student_portal.permissions import IsStudentAdmin, IsBankAdmin
from students.models import StudentUser
from students.serializers import DepositClaimApproveSerializer, ConversionApproveSerializer, ConversionCreateSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser


class DepositClaimsView(APIView):
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


class BDTtoUSDView(APIView):
    http_method_names = ['get', 'post', 'patch']
    permission_classes = [IsBankAdmin | IsStudentAdmin]

    def get(self, request, pk=None, *args, **kwargs):
        query_params = request.query_params.dict()
        student_id = query_params.get("student_id")
        custom_param = None
        if student_id:
            custom_param = {"student_id": student_id}

        response, _ = PriyoPayClient().fetch_conversions(params=custom_param)

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

        serializer = ConversionApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        response, _ = PriyoPayClient().update_conversion(
            conversion_id=conversion_id,
            payload={'request_status': validated_data['request_status'], 'admin_id': request.user.id}
        )
        return Response(response, status=status.HTTP_200_OK)


class USDAccountsView(APIView):
    http_method_names = ['get']
    permission_classes = [IsStudentAdmin | IsBankAdmin]

    def get(self, request, user_id=None, *args, **kwargs):
        """
        Fetch USD accounts from backend
        Supports both list view and detail view by user_id
        """
        if user_id:
            # Get specific account by user_id (treating user_id as account_id)
            response, status_code = PriyoPayClient().fetch_usd_account_by_id(account_id=user_id)
            return Response(response, status=status_code)
        else:
            # Get all accounts with optional query parameters
            query_params = {}

            # Extract query parameters from request
            if request.GET.get('account_status'):
                query_params['account_status'] = request.GET.get('account_status')
            if request.GET.get('student_id'):
                query_params['student_id'] = request.GET.get('student_id')
            if request.GET.get('email_address'):
                query_params['email_address'] = request.GET.get('email_address')
            if request.GET.get('one_auth_uuid'):
                query_params['one_auth_uuid'] = request.GET.get('one_auth_uuid')
            if request.GET.get('limit'):
                query_params['limit'] = request.GET.get('limit')
            if request.GET.get('offset'):
                query_params['offset'] = request.GET.get('offset')

            response, status_code = PriyoPayClient().fetch_usd_accounts(**query_params)
            return Response(response, status=status_code)


class CurrencyConversionView(APIView):
    http_method_names = ['post']
    permission_classes = [IsBankAdmin | IsStudentAdmin]

    def post(self, request, *args, **kwargs):
        """
        Convert currency using /convert-currency/ endpoint
        Expected payload: {
            "from_currency": "BDT",
            "to_currency": "USD", 
            "for_subscription": false,
            "amount": 1
        }
        """
        response, status_code = PriyoPayClient().convert_currency(payload=request.data)
        return Response(response, status=status_code)


class BDTUSDConversionView(APIView):
    http_method_names = ['get', 'post', 'patch']
    permission_classes = [IsBankAdmin | IsStudentAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # Support file uploads

    def get(self, request, pk=None, *args, **kwargs):
        """Fetch BDT to USD conversion requests"""
        response, _ = PriyoPayClient().fetch_bdt_usd_conversions()

        # If pk is provided, return specific conversion
        if pk:
            if response and 'results' in response:
                for conversion in response['results']:
                    if str(conversion.get('id')) == str(pk):
                        return Response(conversion, status=status.HTTP_200_OK)
            return Response({'error': 'Conversion not found'}, status=status.HTTP_404_NOT_FOUND)

        # Otherwise return all conversions
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """Create BDT to USD conversion request with file upload"""
        # Validate input data using your existing serializer
        serializer = ConversionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Extract validated data
        data = {}
        for key, value in serializer.validated_data.items():
            if key != 'expense_document':
                data[key] = value

        # Add admin_id from authenticated user if not provided
        if 'admin_id' not in data:
            data['admin_id'] = request.user.id

        # Handle file upload
        files = {}
        if 'expense_document' in request.FILES:
            files['expense_document'] = request.FILES['expense_document']

        response, status_code = PriyoPayClient().create_bdt_usd_conversion(
            data=data,
            files=files if files else None
        )
        return Response(response, status=status_code)

    def patch(self, request, pk=None, *args, **kwargs):
        """Update BDT to USD conversion request status"""
        conversion_id = pk or request.data.get('conversion_id')
        if not conversion_id:
            return Response(
                {'error': 'conversion_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Prepare payload
        payload = {
            'request_status': request.data.get('request_status'),
            'admin_id': request.data.get('admin_id', request.user.id)
        }

        response, status_code = PriyoPayClient().update_bdt_usd_conversion_status(
            conversion_id=conversion_id,
            payload=payload
        )
        return Response(response, status=status_code)
