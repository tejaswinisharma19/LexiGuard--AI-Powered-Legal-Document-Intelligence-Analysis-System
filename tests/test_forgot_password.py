import pytest
import uuid
from werkzeug.security import generate_password_hash
from app import app, dynamodb_service


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_forgot_password_valid_and_invalid_email(client):
    """Test forgot password request for valid and invalid email addresses."""
    test_email = f"reset_test_{uuid.uuid4().hex[:8]}@example.com"
    user_data = {
        "email": test_email,
        "password_hash": generate_password_hash("OldPassword123"),
        "full_name": "Reset Test User"
    }
    dynamodb_service.save_user(user_data)
    try:
        # Valid email request
        res = client.post("/forgot-password", data={"email": test_email})
        assert res.status_code == 200
        assert b"password reset link has been sent" in res.data

        # User in DB should now have reset token
        updated_user = dynamodb_service.get_user_by_email(test_email)
        assert updated_user.get("reset_token") is not None
        assert updated_user.get("reset_token_used") is False

        # Invalid email request should return generic success message to prevent user enumeration
        res_invalid = client.post("/forgot-password", data={"email": "nonexistent@example.com"})
        assert res_invalid.status_code == 200
        assert b"password reset link has been sent" in res_invalid.data
    finally:
        dynamodb_service.delete_user(test_email)




def test_reset_password_workflow_and_login(client):
    """Test full password reset workflow using token and subsequent login."""
    test_email = f"reset_flow_{uuid.uuid4().hex[:8]}@example.com"
    user_data = {
        "email": test_email,
        "password_hash": generate_password_hash("OldPassword123"),
        "full_name": "Reset Flow User"
    }
    dynamodb_service.save_user(user_data)
    try:
        # Request reset
        client.post("/forgot-password", data={"email": test_email})
        user = dynamodb_service.get_user_by_email(test_email)
        token = user.get("reset_token")
        assert token is not None

        # Access reset page
        res_page = client.get(f"/reset-password/{token}")
        assert res_page.status_code == 200
        assert b"Create a new password" in res_page.data

        # Submit new password
        res_reset = client.post(f"/reset-password/{token}", data={
            "password": "NewSecretPassword123",
            "confirm_password": "NewSecretPassword123"
        })
        assert res_reset.status_code == 200
        assert b"Your password has been reset successfully" in res_reset.data

        # Attempt login with old password (should fail)
        res_old_login = client.post("/login", data={"email": test_email, "password": "OldPassword123"})
        assert b"Invalid email address or password" in res_old_login.data

        # Attempt login with new password (should succeed)
        res_new_login = client.post("/login", data={"email": test_email, "password": "NewSecretPassword123"})
        assert res_new_login.status_code == 302
    finally:
        dynamodb_service.delete_user(test_email)


def test_reset_password_invalid_and_used_token(client):
    """Test reset password with invalid token and used token."""
    res_invalid = client.get("/reset-password/INVALID_TOKEN_123")
    assert res_invalid.status_code == 200
    assert b"invalid or has expired" in res_invalid.data

    # Test single-use token enforcement
    test_email = f"single_use_{uuid.uuid4().hex[:8]}@example.com"
    user_data = {
        "email": test_email,
        "password_hash": generate_password_hash("Pass123456"),
        "full_name": "Single Use User"
    }
    dynamodb_service.save_user(user_data)
    try:
        client.post("/forgot-password", data={"email": test_email})

        user = dynamodb_service.get_user_by_email(test_email)
        token = user.get("reset_token")

        # Use token once
        client.post(f"/reset-password/{token}", data={"password": "NewPass123", "confirm_password": "NewPass123"})

        # Try reusing token (should fail)
        res_reuse = client.get(f"/reset-password/{token}")
        assert b"invalid or has expired" in res_reuse.data
    finally:
        dynamodb_service.delete_user(test_email)
