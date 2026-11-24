import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class BrevoEmailService:
    def __init__(self):
        self.api_instance = None
        if getattr(settings, 'BREVO_API_KEY', None):
            try:
                import sib_api_v3_sdk
                configuration = sib_api_v3_sdk.Configuration()
                configuration.api_key['api-key'] = settings.BREVO_API_KEY
                self.api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
                    sib_api_v3_sdk.ApiClient(configuration)
                )
            except Exception as e:
                logger.warning(f"Could not initialize Brevo API client: {e}")

    def send_transactional_email(self, to_email, to_name, subject, html_content, text_content=None):
        """Send a single transactional email"""
        if not self.api_instance:
            logger.info("Brevo API not configured, skipping Brevo email send")
            return None

        try:
            import sib_api_v3_sdk
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": to_email, "name": to_name}],
                sender={"name": settings.BREVO_FROM_NAME, "email": settings.BREVO_FROM_EMAIL},
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )

            api_response = self.api_instance.send_transac_email(send_smtp_email)
            logger.info(f"Email sent successfully to {to_email}")
            return api_response

        except Exception as e:
            logger.error(f"Exception when sending email via Brevo: {e}")
            return None
