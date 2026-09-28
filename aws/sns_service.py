import logging
import boto3
from config import Config

logger = logging.getLogger(__name__)


class SNSService:
    """
    Service class for sending system/security notifications using AWS SNS.
    """

    def __init__(self, region_name=None, topic_arn=None):
        self.region_name = region_name or getattr(Config, "AWS_REGION", "ap-south-1")
        self.topic_arn = topic_arn
        self.sns_client = boto3.client(
            "sns",
            region_name=self.region_name
        )

    def send_notification(self, subject, message, topic_arn=None):
        """
        Publish a message to an AWS SNS topic.

        Args:
            subject (str): Subject line of the notification.
            message (str): Body content of the notification.
            topic_arn (str, optional): Target SNS Topic ARN. Defaults to configured Topic ARN.

        Returns:
            bool: True if message published successfully, False otherwise.
        """
        target_arn = topic_arn if topic_arn is not None else (self.topic_arn if self.topic_arn is not None else getattr(Config, "SNS_TOPIC_ARN", ""))
        if not target_arn:
            logger.warning("SNS notification skipped: Missing SNS_TOPIC_ARN.")
            return False


        if not subject or not message:
            logger.error("SNS notification failed: Subject and message are required.")
            return False

        try:
            response = self.sns_client.publish(
                TopicArn=target_arn,
                Subject=subject,
                Message=message
            )
            message_id = response.get("MessageId", "N/A")
            logger.info("SNS notification published successfully. MessageId: %s", message_id)
            return True
        except Exception as error:
            logger.error("Failed to publish SNS notification to %s: %s", target_arn, str(error))
            return False

    def send_security_alert(self, user_email, action_type, details=None):
        """
        Send a formatted security alert notification via AWS SNS.

        Args:
            user_email (str): Target email involved in the security action.
            action_type (str): Description of the security action (e.g., 'Password Reset Requested').
            details (str, optional): Additional contextual details.

        Returns:
            bool: True if alert published successfully, False otherwise.
        """
        subject = f"LexiGuard Security Notification — {action_type}"
        message = (
            f"Security Notification from LexiGuard\n\n"
            f"Action: {action_type}\n"
            f"Target Email: {user_email}\n"
        )
        if details:
            message += f"Details: {details}\n"
        message += "\nRegards,\nLexiGuard Security System"

        return self.send_notification(subject, message)

