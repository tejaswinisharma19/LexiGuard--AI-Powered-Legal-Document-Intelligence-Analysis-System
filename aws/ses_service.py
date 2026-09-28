import logging
import boto3
from config import Config

logger = logging.getLogger(__name__)

class SESService:
    """
    Service class for sending transactional emails using AWS SES.
    """

    def __init__(self, region_name=None, sender_email=None):
        self.region_name = region_name or Config.AWS_REGION
        self.sender_email = sender_email or getattr(Config, "SES_SENDER_EMAIL", getattr(Config, "MAIL_DEFAULT_SENDER", "noreply@lexiguard.com"))
        self.ses_client = boto3.client(
            "ses",
            region_name=self.region_name
        )

    def send_password_reset_email(self, to_email, reset_url):
        """
        Send a one-to-one password reset transactional email via AWS SES.

        Args:
            to_email (str): Recipient email address.
            reset_url (str): Password reset URL containing the secure token.

        Returns:
            bool: True if email sent successfully, False otherwise.
        """
        if not to_email or not reset_url:
            logger.error("SES email sending failed: Missing recipient email or reset URL.")
            return False

        subject = "LexiGuard — Password Reset Request"
        body_text = (
            f"Hello,\n\n"
            f"We received a request to reset your LexiGuard password.\n\n"
            f"Use the following link to reset your password:\n\n"
            f"{reset_url}\n\n"
            f"This link expires in 1 hour and can only be used once.\n\n"
            f"If you did not request a password reset, you can safely ignore this email.\n\n"
            f"Regards,\n"
            f"LexiGuard\n"
        )

        try:
            response = self.ses_client.send_email(
                Source=self.sender_email,
                Destination={
                    "ToAddresses": [to_email]
                },
                Message={
                    "Subject": {
                        "Data": subject,
                        "Charset": "UTF-8"
                    },
                    "Body": {
                        "Text": {
                            "Data": body_text,
                            "Charset": "UTF-8"
                        }
                    }
                }
            )
            logger.info("Password reset email successfully sent via SES.")
            return True
        except Exception as error:
            logger.error("Failed to send password reset email via AWS SES: %s", str(error))
            return False

