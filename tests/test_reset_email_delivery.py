import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash

import app as app_module
from app import app, dynamodb_service

class TestPasswordResetEmailDelivery(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test-secret-key"
        self.client = app.test_client()
        self.test_email = "smtp_delivery_user@example.com"
        self.test_password = "OldPassword123!"
        self.test_name = "SMTP Delivery User"

        dynamodb_service.save_user({
            "email": self.test_email,
            "password_hash": generate_password_hash(self.test_password),
            "full_name": self.test_name
        })

    def tearDown(self):
        with dynamodb_service._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM users WHERE email = %s;", (self.test_email,))

    def test_1_forgot_password_get_works(self):
        """1. Forgot-password GET works."""
        res = self.client.get("/forgot-password")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Reset your password", res.data)

    def test_2_3_4_forgot_password_post_generates_and_saves_token(self):
        """2, 3, 4. Forgot-password POST generates, saves token in DynamoDB, and builds reset URL."""
        with patch.object(app_module.gmail_service, "send_password_reset_email", return_value=True) as mock_send:
            res = self.client.post("/forgot-password", data={"email": self.test_email})
            self.assertEqual(res.status_code, 200)

            user = dynamodb_service.get_user_by_email(self.test_email)
            self.assertIsNotNone(user.get("reset_token"))
            self.assertFalse(user.get("reset_token_used"))
            self.assertIsNotNone(user.get("reset_token_expires"))

    def test_5_gmail_smtp_called_with_recipient_and_reset_url(self):
        """5. Gmail SMTP service is called with correct recipient and reset URL."""
        with patch.object(app_module.gmail_service, "send_password_reset_email", return_value=True) as mock_send:
            res = self.client.post("/forgot-password", data={"email": self.test_email})
            self.assertEqual(res.status_code, 200)

            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            self.assertEqual(call_args[0], self.test_email)
            self.assertIn("/reset-password/", call_args[1])

    def test_8_reset_password_url_opens_successfully(self):
        """8. Reset-password URL opens successfully."""
        with patch.object(app_module.gmail_service, "send_password_reset_email", return_value=True):
            self.client.post("/forgot-password", data={"email": self.test_email})
            user = dynamodb_service.get_user_by_email(self.test_email)
            token = user.get("reset_token")

            res = self.client.get(f"/reset-password/{token}")
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Create a new password", res.data)

    def test_9_invalid_token_is_rejected(self):
        """9. Invalid token is rejected."""
        res = self.client.get("/reset-password/INVALID_TOKEN_99999")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"invalid or has expired", res.data)

    def test_10_expired_token_is_rejected(self):
        """10. Expired token is rejected."""
        token = "expired_token_12345"
        expired_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        dynamodb_service.save_reset_token(self.test_email, token, expired_time)

        res = self.client.get(f"/reset-password/{token}")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"has expired", res.data)

    def test_11_12_password_reset_and_subsequent_login(self):
        """11, 12. Password can be reset with valid token and login works with new password."""
        with patch.object(app_module.gmail_service, "send_password_reset_email", return_value=True):
            self.client.post("/forgot-password", data={"email": self.test_email})
            user = dynamodb_service.get_user_by_email(self.test_email)
            token = user.get("reset_token")

            new_pass = "BrandNewSecretPassword123!"
            res_post = self.client.post(f"/reset-password/{token}", data={
                "password": new_pass,
                "confirm_password": new_pass
            })
            self.assertEqual(res_post.status_code, 200)
            self.assertIn(b"Your password has been reset successfully", res_post.data)

            # Login with old password fails
            res_old = self.client.post("/login", data={"email": self.test_email, "password": self.test_password})
            self.assertIn(b"Invalid email address or password", res_old.data)

            # Login with new password succeeds
            res_new = self.client.post("/login", data={"email": self.test_email, "password": new_pass})
            self.assertEqual(res_new.status_code, 302)

    def test_13_login_register_logout_flow_remains_intact(self):
        """13. Existing login/register/logout functionality remains intact."""
        logout_res = self.client.get("/logout")
        self.assertEqual(logout_res.status_code, 302)

        import uuid
        reg_email = f"new_registered_user_{uuid.uuid4().hex[:8]}@example.com"
        try:
            reg_res = self.client.post("/register", data={
                "full_name": "New Reg User",
                "email": reg_email,
                "password": "Password123!",
                "confirm_password": "Password123!"
            })
            self.assertEqual(reg_res.status_code, 302)

            db_user = dynamodb_service.get_user_by_email(reg_email)
            self.assertIsNotNone(db_user)
            self.assertEqual(db_user["full_name"], "New Reg User")
        finally:
            with dynamodb_service._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM users WHERE email = %s;", (reg_email,))

if __name__ == "__main__":
    unittest.main()
