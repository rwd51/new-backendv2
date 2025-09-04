import requests
from django.conf import settings
from django.utils import timezone

from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from bank_admin.models import BankAdminUser
from bank_admin.serializers import SignupSerializer, SigninSerializer, BankAdminUserSerializer, \
    BankAdminApprovalSerializer
from bank_admin.supabase_client import supabase
from bank_admin.permissions import IsSupabaseAuthenticated
from student_admin.serializers import BdBankSerializer
from student_portal.permissions import IsAnyAdmin, IsBankAdmin


class AuthViewSet(viewsets.ViewSet):

    def signup(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        bd_bank = serializer.validated_data["bd_bank"]
        first_name = serializer.validated_data["first_name"]
        last_name = serializer.validated_data["last_name"]

        # Create user in Supabase
        result = supabase.auth.sign_up({
            "email": email,
            "password": password
        })

        if result.user is None:
            return Response({"error": "Failed to create Supabase user"}, status=status.HTTP_400_BAD_REQUEST)

        # Save user in Django DB
        admin_user, created = BankAdminUser.objects.get_or_create(
            user_id=result.user.id,
            defaults={
                "email": email,
                "bd_bank": bd_bank,
                "first_name": first_name,
                "last_name": last_name
            }
        )

        return Response(BankAdminUserSerializer(admin_user).data, status=status.HTTP_201_CREATED)

    def signin(self, request):
        serializer = SigninSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        try:
            result = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
        except Exception as ex:
            return Response({"message": f"{ex}"}, status=status.HTTP_400_BAD_REQUEST)

        if not result.user.confirmed_at:
            return Response({"message": "Please confirm your email before signing in."}, status=400)

        if result.session is None:
            return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        admin_user = BankAdminUser.objects.filter(user_id=result.user.id, email=email).first()
        if admin_user:
            if not admin_user.is_approved:
                err_dict = {"message": "Your account requires approval from another admin before you can sign in."}
                return Response(err_dict, status=400)
            if not admin_user.is_email_verified and result.user.confirmed_at:
                admin_user.is_email_verified = True
                admin_user.save(update_fields=["is_email_verified"])
        else:
            return Response({"error": "Admin user not exists in student portal."}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({
            "access_token": result.session.access_token,
            "refresh_token": result.session.refresh_token,
            "user_id": result.user.id,
            "email": admin_user.email,
            "first_name": admin_user.first_name,
            "last_name": admin_user.last_name,
            "bd_bank": BdBankSerializer(admin_user.bd_bank).data if admin_user.bd_bank else None
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def refresh(self, request):
        """Use Supabase refresh_token to get new access token."""
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response({"error": "Refresh token required"}, status=400)

        url = f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=refresh_token"
        headers = {"apikey": settings.SUPABASE_SERVICE_ROLE_KEY, "Content-Type": "application/json"}
        data = {"refresh_token": refresh_token}

        res = requests.post(url, headers=headers, json=data)
        return Response(res.json(), status=res.status_code)

    @action(detail=False, methods=["post"])
    def logout(self, request):
        """Invalidate Supabase session using access_token."""
        access_token = request.data.get("access_token")
        if not access_token:
            return Response({"error": "Access token required"}, status=400)

        url = f"{settings.SUPABASE_URL}/auth/v1/logout"
        headers = {"apikey": settings.SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {access_token}"}

        res = requests.post(url, headers=headers)
        if res.status_code == 204:
            return Response({"message": "Logged out successfully"})
        return Response(res.json(), status=res.status_code)


class BankAdminApprovalViewSet(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = BankAdminUser.objects.all()
    serializer_class = BankAdminApprovalSerializer
    permission_classes = [IsBankAdmin | IsSupabaseAuthenticated]

    def update(self, request, *args, **kwargs):
        if request.method.lower() == "put":
            return Response({"detail": "PUT not allowed. Use PATCH instead."}, status=405)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        serializer.save(approved_by=request.user, approved_at=timezone.now())
        return Response(self.get_serializer(serializer.instance).data, status=status.HTTP_200_OK)


class BankAdminListViewSet(viewsets.ReadOnlyModelViewSet):
    http_method_names = ['get']
    queryset = BankAdminUser.objects.all()
    serializer_class = BankAdminUserSerializer
    permission_classes = [IsAnyAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return self.queryset.none()

        token_type = getattr(self.request.user, 'token_type', None)
        if token_type == 'local_admin':
            return self.queryset.all()
        elif token_type == 'bank_admin':
            return self.queryset.filter(bd_bank=self.request.user.bd_bank)

        return self.queryset.none()
