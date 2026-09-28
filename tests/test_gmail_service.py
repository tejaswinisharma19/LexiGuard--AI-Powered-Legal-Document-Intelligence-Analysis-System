import unittest
from unittest.mock import MagicMock, patch

import pytest
from app import app
from config import Config
from services.gmail_service import GmailService


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestGmailService(unittest.TestCase):
    def test_gmail_service_init_and_config(self):
        service = GmailService(
            server="smtp.gmail.com",
            port=587,
            username="testuser@gmail.com",
            password="app_password_123",
            use_tls=True,
            default_sender="LexiGuard <noreply@lexiguard.com>"
        )
        self.assertEqual(service.server, "smtp.gmail.com")
        self.assertEqual(service.port, 587)
        self.assertEqual(service.username, "testuser@gmail.com")
        self.assertEqual(service.password, "app_password_123")
        self.assertTrue(service.use_tls)
        self.assertTrue(service.is_configured())

    def test_gmail_service_not_configured_when_empty(self):
        service = GmailService(username="", password="")
        self.assertFalse(service.is_configured())
        result = service.send_password_reset_email("recipient@example.com", "http://localhost/reset/token123")
        self.assertFalse(result)

    @patch("smtplib.SMTP")
    def test_send_password_reset_email_success(self, mock_smtp_class):
        mock_smtp_instance = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp_instance

        service = GmailService(
            server="smtp.gmail.com",
            port=587,
            username="sender@gmail.com",
            password="app_password_123",
            use_tls=True
        )

        res = service.send_password_reset_email("user@example.com", "http://localhost:5000/reset-password/abc123token")
        self.assertTrue(res)

        mock_smtp_class.assert_called_once_with("smtp.gmail.com", 587, timeout=10)
        mock_smtp_instance.starttls.assert_called_once()
        mock_smtp_instance.login.assert_called_once_with("sender@gmail.com", "app_password_123")
        mock_smtp_instance.send_message.assert_called_once()

        sent_msg = mock_smtp_instance.send_message.call_args[0][0]
        self.assertEqual(sent_msg["Subject"], "LexiGuard — Password Reset Request")
        self.assertEqual(sent_msg["To"], "user@example.com")


def test_forgot_password_triggers_gmail_service(client):
    """Verify forgot-password flow invokes gmail_service and returns generic response."""
    import extensions
    with patch.object(extensions.gmail_service, "send_password_reset_email", return_value=True) as mock_send:
        res = client.post("/forgot-password", data={"email": "sharmatejaswini21@gmail.com"})
        assert res.status_code == 200
        assert b"password reset link has been sent" in res.data
        mock_send.assert_called_once()
        called_args = mock_send.call_args[0]
        assert called_args[0] == "sharmatejaswini21@gmail.com"
        assert "/reset-password/" in called_args[1]

