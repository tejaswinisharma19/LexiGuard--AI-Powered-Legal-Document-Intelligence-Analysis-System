import unittest
from app import app
from services.postgresql_service import PostgreSQLService
from config import Config
from werkzeug.security import check_password_hash


class TestAuthSystem(unittest.TestCase):
    """
    Test suite for LexiGuard authentication flow including user registration,
    login, password hashing, route protection, and logout.
    """

    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.app.config["SECRET_KEY"] = "test-secret-key"
        self.client = self.app.test_client()
        self.postgresql_service = PostgreSQLService()
        self.test_email = "test.user.auth@example.com"
        self.test_password = "SecurePassword123!"
        self.test_name = "Test Auth User"

    def tearDown(self):
        # Clean up test user from PostgreSQL
        try:
            with self.postgresql_service._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM users WHERE email = %s", (self.test_email,))
        except Exception as e:
            print(f"Cleanup error: {e}")

    def test_unauthenticated_access(self):
        """Unauthenticated GET to / should redirect to /login."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.location)

    def test_unauthenticated_api_access(self):
        """Unauthenticated GET to /api/documents should return 401 JSON error."""
        response = self.client.get("/api/documents")
        self.assertEqual(response.status_code, 401)
        json_data = response.get_json()
        self.assertIn("error", json_data)

    def test_user_registration_and_login_flow(self):
        """Test registration, password hashing, login, session retention, and logout."""
        # 1. Register new user
        reg_response = self.client.post(
            "/register",
            data={
                "full_name": self.test_name,
                "email": self.test_email,
                "password": self.test_password,
                "confirm_password": self.test_password,
            },
            follow_redirects=False,
        )
        self.assertEqual(reg_response.status_code, 302)
        self.assertIn("/", reg_response.location)

        # 2. Check user saved in PostgreSQL with hashed password
        user = self.postgresql_service.get_user_by_email(self.test_email)
        self.assertIsNotNone(user)
        self.assertEqual(user["email"], self.test_email)
        self.assertEqual(user["full_name"], self.test_name)
        self.assertNotEqual(user["password_hash"], self.test_password)
        self.assertTrue(check_password_hash(user["password_hash"], self.test_password))

        # 3. Access protected route with active session from registration
        home_response = self.client.get("/")
        self.assertEqual(home_response.status_code, 200)
        self.assertIn("Test Auth User", home_response.get_data(as_text=True))

        # 4. Logout
        logout_response = self.client.get("/logout")
        self.assertEqual(logout_response.status_code, 302)

        # 5. Access home page after logout -> should redirect to login
        home_after_logout = self.client.get("/")
        self.assertEqual(home_after_logout.status_code, 302)

        # 6. Login with correct credentials
        login_response = self.client.post(
            "/login",
            data={
                "email": self.test_email,
                "password": self.test_password,
            },
            follow_redirects=False,
        )
        self.assertEqual(login_response.status_code, 302)

        # 7. Login with invalid password
        self.client.get("/logout")
        bad_login = self.client.post(
            "/login",
            data={
                "email": self.test_email,
                "password": "WrongPassword",
            },
        )
        self.assertEqual(bad_login.status_code, 200)
        self.assertIn("Invalid email address or password", bad_login.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
