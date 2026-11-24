from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from apps.core.utils.brevo_service import BrevoEmailService
import logging

logger = logging.getLogger(__name__)


def send_otp_email(user, otp_code, purpose):
    """
    Sends verification or password reset OTP emails using Brevo if configured,
    or falls back to Django standard email backend (e.g. smtp4dev in development).
    """
    subject = (
        "Verification Code" if purpose == "verification" else "Password Reset Code"
    )

    context = {
        "user": user,
        "otp": otp_code,
        "purpose": purpose,
        "valid_minutes": 10
    }

    text_content = render_to_string("accounts/otp_email.txt", context)
    html_content = render_to_string("accounts/otp_email.html", context)

    # Always log OTP to server console/logs so it is immediately visible in docker logs
    print(f"\n========================================\n🔑 [OTP CODE] Purpose: {purpose.upper()} | Email: {user.email} | OTP: {otp_code}\n========================================\n", flush=True)
    logger.info(f"🔑 [OTP CODE] Purpose: {purpose} | Email: {user.email} | OTP: {otp_code}")

    # 1. Try Brevo if API key is provided
    if getattr(settings, 'BREVO_API_KEY', None):
        brevo_service = BrevoEmailService()
        to_name = getattr(user.profile, 'name', '') if hasattr(user, 'profile') and user.profile.name else ''
        res = brevo_service.send_transactional_email(
            to_email=user.email,
            to_name=to_name,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
        if res is not None:
            return res

    # 2. Fallback to standard Django mail
    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        return email.send(fail_silently=False)
    except Exception as e:
        print(f"❌ [EMAIL DELIVERY ERROR] Failed to deliver email to {user.email}: {e}", flush=True)
        logger.error(f"Failed to send email to {user.email}: {e}")
        return None
