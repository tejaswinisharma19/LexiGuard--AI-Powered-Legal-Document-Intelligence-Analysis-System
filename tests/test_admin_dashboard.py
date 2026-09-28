import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"
    with app.test_client() as client:
        yield client


def test_admin_dashboard_unauthenticated_redirect(client):
    """Test unauthenticated user redirected or receiving 401 on /admin."""
    res_page = client.get("/admin")
    assert res_page.status_code in [302, 401]

    res_api = client.get("/api/admin/stats")
    assert res_api.status_code == 401


def test_admin_dashboard_normal_user_forbidden(client):
    """Test normal authenticated user receiving 403 Forbidden on admin endpoints."""
    with client.session_transaction() as sess:
        sess["user_id"] = "regular_user@lexiguard.com"

    res_page = client.get("/admin")
    assert res_page.status_code == 403

    res_api = client.get("/api/admin/stats")
    assert res_api.status_code == 403


def test_old_admin_email_forbidden(client):
    """Test old admin@lexiguard.com email is rejected with 403 Forbidden."""
    with client.session_transaction() as sess:
        sess["user_id"] = "admin@lexiguard.com"

    res_page = client.get("/admin")
    assert res_page.status_code == 403

    res_api = client.get("/api/admin/stats")
    assert res_api.status_code == 403


def test_admin_dashboard_admin_access(client):
    """Test lexiguard662@gmail.com gaining access to /admin and /api/admin/stats."""
    with client.session_transaction() as sess:
        sess["user_id"] = "lexiguard662@gmail.com"

    res_page = client.get("/admin")
    assert res_page.status_code == 200
    assert b"Admin Overview" in res_page.data

    res_api = client.get("/api/admin/stats")
    assert res_api.status_code == 200
    data = res_api.get_json()
    assert "total_users" in data
    assert "total_documents" in data
    assert "total_analyses" in data
    assert "total_comparisons" in data
    assert "recent_activity" in data
