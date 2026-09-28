import unittest
from unittest.mock import patch, MagicMock

import app as app_module
from app import app, dynamodb_service
from aws.ses_service import SESService


class TestSESService(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test-secret-key"
        self.client = app.test_client()
        self.test_email = "test_ses_user@example.com"

        dynamodb_service.save_user({
            "email": self.test_email,
            "password_hash": "pbkdf2:sha256:fakehash",
            "full_name": "SES Test User"
        })

    def tearDown(self):
        with dynamodb_service._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM users WHERE email = %s;", (self.test_email,))

    def test_ses_service_direct_unit_test(self):
        """Direct unit test for legacy SESService using mocked boto3 client."""
        service = SESService(region_name="us-east-1", sender_email="noreply@lexiguard.com")
        mock_ses = MagicMock()
        mock_ses.send_email.return_value = {"MessageId": "msg-12345"}
        service.ses_client = mock_ses

        success = service.send_password_reset_email("user@example.com", "http://localhost/reset/token123")

        self.assertTrue(success)
        mock_ses.send_email.assert_called_once()
        call_kwargs = mock_ses.send_email.call_args[1]
        self.assertEqual(call_kwargs["Source"], "noreply@lexiguard.com")
        self.assertEqual(call_kwargs["Destination"]["ToAddresses"], ["user@example.com"])
        self.assertIn("http://localhost/reset/token123", call_kwargs["Message"]["Body"]["Text"]["Data"])

    def test_forgot_password_no_longer_calls_ses(self):
        """Verify forgot password flow uses GmailService and does NOT call SES."""
        mock_ses = MagicMock()
        with patch.object(app_module.ses_service, "ses_client", mock_ses), \
             patch.object(app_module.gmail_service, "send_password_reset_email", return_value=True) as mock_gmail:

            res = self.client.post("/forgot-password", data={"email": self.test_email})
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"password reset link has been sent", res.data)
            mock_ses.send_email.assert_not_called()
            mock_gmail.assert_called_once()


if __name__ == "__main__":
    unittest.main()
