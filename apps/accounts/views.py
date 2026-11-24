from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import check_password
from django.conf import settings
from django.core.cache import cache
import uuid
import logging

logger = logging.getLogger(__name__)

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.apple.views import AppleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView

from apps.core.utils.mixins import BaseResponseMixin
from apps.accounts.utils.event_auth_helpers import (
    resolve_event,
    is_user_verified_for_event,
    mark_user_verified_for_event,
)
from .models import UserProfile
from .serializers import (
    RegisterSerializer,
    VerifyEmailSerializer,
    PasswordResetRequestSerializer,
    PasswordResetOTPVerifySerializer,
    PasswordResetConfirmSerializer,
    ChangePasswordSerializer,
    ResendOTPSerializer,
    AccountSoftDeleteSerializer,
    ParmanentAccountDeleteSerializer,
    AccountRestoreSerializer,
    ProfileUpdateSerializer,
    VerifyEmailChangeSerializer,
    LoginSerializer,
    SocialAuthSerializer,
    UserProfileSerializer,
)

User = get_user_model()


class RegisterView(BaseResponseMixin, generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [AnonRateThrottle]

    def create(self, request, *args, **kwargs):
        email = (request.data.get("email") or "").strip().lower()
        access_code = request.data.get("access_code") or request.data.get("event_access_code")
        event_id = request.data.get("event_id")

        if not email:
            return self.error_response(message="Email is required", status_code=status.HTTP_400_BAD_REQUEST)

        event = resolve_event(request, access_code=access_code, event_id=event_id, email=email)
        user = User.objects.filter(email=email).first()

        # Check if already verified for this event
        if is_user_verified_for_event(email, event, user=user):
            if not user:
                temp_pw = f"Pass-{uuid.uuid4().hex[:12]}!"
                user = User.objects.create(email=email, is_active=True)
                user.set_password(temp_pw)
                user.save()
            elif not user.is_active:
                user.is_active = True
                user.save()

            mark_user_verified_for_event(email, event, user=user)
            refresh = RefreshToken.for_user(user)
            print(f"✅ [Register] User '{email}' already verified for '{event.name if event else 'Event'}'. Bypassing OTP.", flush=True)

            return self.success_response(
                data={
                    "email": user.email,
                    "is_sent": False,
                    "already_verified": True,
                    "tokens": {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    },
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "event_id": event.id if event else None,
                    "event_name": event.name if event else None,
                    "access_code": event.access_code if event else None,
                },
                message="Welcome back! You are already verified for this event.",
                status_code=status.HTTP_200_OK,
            )

        # User is NOT verified for this event -> Send OTP
        if not user:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
            else:
                temp_pw = f"Pass-{uuid.uuid4().hex[:12]}!"
                user = User.objects.create(email=email, is_active=False)
                user.set_password(temp_pw)
                user.save()
                reg_ser = RegisterSerializer()
                reg_ser.send_verification_otp(user)
        else:
            reg_ser = RegisterSerializer()
            reg_ser.send_verification_otp(user)

        if event:
            cache.set(f"pending_event_{email}", event.id, timeout=3600)

        print(f"📩 [Register] User '{email}' needs verification for '{event.name if event else 'Event'}'. OTP sent.", flush=True)

        return self.success_response(
            data={
                "email": user.email,
                "is_sent": True,
                "already_verified": False,
                "event_id": event.id if event else None,
                "event_name": event.name if event else None,
            },
            message="OTP sent to your email. Please check your inbox for verification code.",
            status_code=status.HTTP_200_OK,
        )


class VerifyEmailView(BaseResponseMixin, generics.GenericAPIView):
    serializer_class = VerifyEmailSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        email = user.email.strip().lower()
        access_code = serializer.validated_data.get("access_code")
        event_id = serializer.validated_data.get("event_id")

        # Resolve event and mark user verified for this event
        event = resolve_event(request, access_code=access_code, event_id=event_id, email=email)
        ticket = None
        if event:
            ticket = mark_user_verified_for_event(email, event, user=user)
            print(f"🎉 [VerifyEmail] User '{email}' verified for event '{event.name}'. Ticket: {ticket.ticket_id if ticket else 'N/A'}", flush=True)

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "success": True,
                "message": "Email verified successfully",
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                "already_verified": True,
                "user": {
                    "id": user.id,
                    "email": user.email,
                },
                "event": {
                    "id": event.id if event else None,
                    "name": event.name if event else None,
                    "access_code": event.access_code if event else None,
                } if event else None,
                "ticket": {
                    "id": ticket.id if ticket else None,
                    "ticket_id": ticket.ticket_id if ticket else None,
                    "seat_no": ticket.seat_no if ticket else None,
                } if ticket else None,
            },
            status=status.HTTP_200_OK,
        )


class ResendOTPView(BaseResponseMixin, generics.GenericAPIView):
    serializer_class = ResendOTPSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].strip().lower()
        purpose = serializer.validated_data["purpose"]
        access_code = serializer.validated_data.get("access_code")
        event_id = serializer.validated_data.get("event_id")

        try:
            print(f"📩 [ResendOTP Request] Email: {email} | Purpose: {purpose}", flush=True)
            user = User.objects.filter(email=email).first()

            if user and user.is_blocked:
                return self.error_response(
                    message="Your account has been suspended. Please contact support.",
                    status_code=status.HTTP_403_FORBIDDEN
                )

            if purpose == "verification":
                event = resolve_event(request, access_code=access_code, event_id=event_id, email=email)

                # Check if already verified for this event
                if is_user_verified_for_event(email, event, user=user):
                    if not user:
                        temp_pw = f"Pass-{uuid.uuid4().hex[:12]}!"
                        user = User.objects.create(email=email, is_active=True)
                        user.set_password(temp_pw)
                        user.save()
                    elif not user.is_active:
                        user.is_active = True
                        user.save()

                    mark_user_verified_for_event(email, event, user=user)
                    refresh = RefreshToken.for_user(user)
                    print(f"✅ [ResendOTP] User '{email}' already verified for '{event.name if event else 'Event'}'. Bypassing OTP.", flush=True)

                    return self.success_response(
                        data={
                            "email": user.email,
                            "is_sent": False,
                            "already_verified": True,
                            "tokens": {
                                "refresh": str(refresh),
                                "access": str(refresh.access_token),
                            },
                            "refresh": str(refresh),
                            "access": str(refresh.access_token),
                            "event_id": event.id if event else None,
                            "event_name": event.name if event else None,
                            "access_code": event.access_code if event else None,
                        },
                        message="Welcome back! You are already verified for this event.",
                        status_code=status.HTTP_200_OK,
                    )

                # Not verified for this event -> Send OTP
                if not user:
                    temp_pw = f"Pass-{uuid.uuid4().hex[:12]}!"
                    user = User.objects.create(email=email, is_active=False)
                    user.set_password(temp_pw)
                    user.save()

                if event:
                    cache.set(f"pending_event_{email}", event.id, timeout=3600)

                register_serializer = RegisterSerializer()
                register_serializer.send_verification_otp(user)

                print(f"📩 [ResendOTP] User '{email}' needs verification for '{event.name if event else 'Event'}'. Sent OTP.", flush=True)

                return self.success_response(
                    data={
                        "email": email,
                        "is_sent": True,
                        "already_verified": False,
                        "event_id": event.id if event else None,
                        "event_name": event.name if event else None,
                    },
                    message=f"OTP has been sent to your email for {event.name if event else 'event'}."
                )

            elif purpose == "password_reset":
                reset_serializer = PasswordResetRequestSerializer()
                reset_serializer.send_reset_otp(email)
                return self.success_response(
                    message="Password reset OTP has been sent to your email"
                )

        except Exception as e:
            logger.error(f"Error in ResendOTPView: {e}")
            return self.error_response(message="An error occurred while processing your request.")


class LoginView(BaseResponseMixin, generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get("email")
        password = serializer.validated_data.get("password")

        try:
            user = User.objects.get(email=email)
            if user.is_blocked:
                return self.error_response(
                    message="Your account has been suspended. Please contact support.",
                    status_code=status.HTTP_403_FORBIDDEN
                )
        except User.DoesNotExist:
            pass

        user = authenticate(username=email, password=password)

        if user is not None:
            if user.is_blocked:
                return self.error_response(
                    message="Your account has been suspended. Please contact support.",
                    status_code=status.HTTP_403_FORBIDDEN
                )

            if not user.is_active:
                return self.error_response(
                    message="Please verify your email before logging in",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            refresh = RefreshToken.for_user(user)
            return self.success_response(
                data={
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user": {
                        "id": user.id,
                        "email": user.email,
                    }
                },
                message="Login successful"
            )
        else:
            return self.error_response(
                message="Invalid email or password",
                status_code=status.HTTP_401_UNAUTHORIZED
            )


class LogoutView(BaseResponseMixin, generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = [UserRateThrottle]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return self.error_response(
                    message="Refresh token is required",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            return self.success_response(
                message="Logged out successfully",
                status_code=status.HTTP_200_OK
            )
        except Exception:
            return self.error_response(
                message="Invalid or expired refresh token",
                status_code=status.HTTP_400_BAD_REQUEST
            )


class PasswordResetRequestView(BaseResponseMixin, generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        serializer.send_reset_otp(email)

        return self.success_response(
            message="If the email exists, a password reset OTP has been sent",
            status_code=status.HTTP_200_OK,
        )


class PasswordResetOTPVerifyView(BaseResponseMixin, generics.GenericAPIView):
    serializer_class = PasswordResetOTPVerifySerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return self.success_response(
            data={"email": serializer.validated_data["email"]},
            message="OTP verified successfully",
            status_code=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(BaseResponseMixin, generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return self.success_response(
            message="Password has been reset successfully",
            status_code=status.HTTP_200_OK,
        )


class ChangePasswordView(BaseResponseMixin, generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = [UserRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        old_password = serializer.validated_data["old_password"]
        new_password = serializer.validated_data["new_password"]

        if not check_password(old_password, user.password):
            return self.error_response(
                message="Current password is incorrect",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        return self.success_response(
            message="Password changed successfully"
        )


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = getattr(settings, "GOOGLE_CALLBACK_URL", "")


class AppleLogin(SocialLoginView):
    adapter_class = AppleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = getattr(settings, "APPLE_CALLBACK_URL", "")


class AccountSoftDeleteView(BaseResponseMixin, APIView):
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = [UserRateThrottle]

    def post(self, request):
        serializer = AccountSoftDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.soft_delete()

        return self.success_response(
            message="Account has been deactivated successfully"
        )


class ParmanentAccountDeleteView(BaseResponseMixin, APIView):
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = [UserRateThrottle]

    def post(self, request):
        serializer = ParmanentAccountDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.delete()

        return self.success_response(
            message="Account has been deleted successfully"
        )


class DeleteUserDataView(BaseResponseMixin, APIView):
    """
    Public and App API to delete all user data and permanently delete user account.
    Designed specifically for Apple App Store and Google Play Store data deletion requirement.
    Accepts: { "email": "user@example.com" } or authenticated user Bearer token.
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get("email")
        if not email and request.user.is_authenticated:
            email = request.user.email

        if not email:
            return self.error_response(
                message="User email is required to delete user data",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        email = email.strip().lower()
        try:
            user = User.objects.get(email=email)
            user.delete()
            return self.success_response(
                data={"email": email, "deleted": True},
                message=f"All data and account for {email} have been permanently deleted successfully."
            )
        except User.DoesNotExist:
            return self.error_response(
                message=f"No user account found with email: {email}",
                status_code=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request):
        return self.post(request)


class AccountRestoreView(BaseResponseMixin, APIView):
    permission_classes = (permissions.IsAdminUser,)

    def post(self, request):
        serializer = AccountRestoreSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(
                message="Invalid data provided",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        user = serializer.user
        user.restore()

        return self.success_response(
            data={"email": user.email},
            message="Account restored successfully"
        )


class ProfileUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileUpdateSerializer

    def get_object(self):
        return self.request.user.profile

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        instance, email_changed = serializer.save()

        response_data = self.get_serializer(instance).data

        if email_changed:
            response_data["email_verification_pending"] = True
            response_data["message"] = (
                "Profile updated. Please verify your new email address with the code sent."
            )
        else:
            response_data["message"] = "Profile updated successfully."

        return Response(response_data)


class VerifyEmailChangeView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VerifyEmailChangeSerializer

    def post(self, request):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Email successfully updated."}, status=status.HTTP_200_OK
        )


class SocialAuthView(BaseResponseMixin, generics.GenericAPIView):
    serializer_class = SocialAuthSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.create_or_login_user()
        refresh = RefreshToken.for_user(user)

        return self.success_response(
            data={
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.profile.name if hasattr(user, "profile") else "",
                    "social_auth_provider": user.social_auth_provider,
                },
            },
            message="Login successful",
            status_code=status.HTTP_200_OK,
        )


class UserProfileGenericView(BaseResponseMixin, RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.get_serializer(profile)

        return self.success_response(
            data=serializer.data,
            message="Profile retrieved successfully"
        )

    def put(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return self.success_response(
                data=serializer.data,
                message='Profile updated successfully'
            )

        errors = serializer.errors
        if 'gender' in errors:
            valid_genders = [choice[0] for choice in UserProfile.GENDER_CHOICES]
            errors['gender_choices'] = valid_genders

        return self.error_response(
            message="Validation failed",
            errors=errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    def post(self, request, *args, **kwargs):
        return self.put(request, *args, **kwargs)
