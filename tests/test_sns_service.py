import unittest
from unittest.mock import patch, MagicMock

import app as app_module
from app import app, dynamodb_service
from config import Config
from aws.sns_service import SNSService


class TestSNSService(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test-secret-key"
        self.client = app.test_client()
        self.test_email = "test_sns_user@example.com"

        dynamodb_service.save_user({
            "email": self.test_email,
            "password_hash": "pbkdf2:sha256:fakehash",
            "full_name": "SNS Test User"
        })

    def test_sns_service_direct_unit_test(self):
        """Direct unit test for SNSService using mocked boto3 client."""
        service = SNSService(region_name="ap-south-1", topic_arn="arn:aws:sns:ap-south-1:123456789012:LexiGuardNotifications")
        mock_sns = MagicMock()
        mock_sns.publish.return_value = {"MessageId": "msg-sns-12345"}
        service.sns_client = mock_sns

        success = service.send_notification("Test Subject", "Test Message Body")

        self.assertTrue(success)
        mock_sns.publish.assert_called_once_with(
            TopicArn="arn:aws:sns:ap-south-1:123456789012:LexiGuardNotifications",
            Subject="Test Subject",
            Message="Test Message Body"
        )

    def test_sns_service_missing_topic_arn(self):
        """Returns False gracefully when topic_arn is missing or empty."""
        service = SNSService(region_name="ap-south-1", topic_arn="")
        mock_sns = MagicMock()
        service.sns_client = mock_sns

        with patch.object(Config, "SNS_TOPIC_ARN", ""):
            success = service.send_notification("Subject", "Message")
            self.assertFalse(success)
            mock_sns.publish.assert_not_called()

    def test_sns_service_publish_failure(self):
        """Returns False when boto3 sns publish raises an exception."""
        service = SNSService(region_name="ap-south-1", topic_arn="arn:aws:sns:ap-south-1:123:Topic")
        mock_sns = MagicMock()
        mock_sns.publish.side_effect = Exception("AWS SNS Connection Failed")
        service.sns_client = mock_sns

        success = service.send_notification("Subject", "Message")
        self.assertFalse(success)

    def test_sns_security_alert(self):
        """Test send_security_alert formats security notification correctly on shared topic."""
        service = SNSService(region_name="ap-south-1", topic_arn="arn:aws:sns:ap-south-1:123:LexiGuardNotifications")
        mock_sns = MagicMock()
        mock_sns.publish.return_value = {"MessageId": "msg-sec-999"}
        service.sns_client = mock_sns

        success = service.send_security_alert("user@example.com", "System Alert")
        self.assertTrue(success)
        mock_sns.publish.assert_called_once()
        call_kwargs = mock_sns.publish.call_args[1]
        self.assertEqual(call_kwargs["TopicArn"], "arn:aws:sns:ap-south-1:123:LexiGuardNotifications")
        self.assertIn("System Alert", call_kwargs["Subject"])
        self.assertIn("Target Email: user@example.com", call_kwargs["Message"])

    def test_forgot_password_does_not_call_sns(self):
        """Verify forgot-password flow uses GmailService and does NOT call SNS."""
        mock_sns = MagicMock()
        with patch.object(app_module.sns_service, "sns_client", mock_sns), \
             patch.object(app_module.gmail_service, "send_password_reset_email", return_value=True):

            res = self.client.post("/forgot-password", data={"email": self.test_email})
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"password reset link has been sent", res.data)
            mock_sns.publish.assert_not_called()


if __name__ == "__main__":
    unittest.main()
