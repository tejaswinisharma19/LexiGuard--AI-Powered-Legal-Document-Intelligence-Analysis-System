import pytest
from app import app, dynamodb_service


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_admin_portal_unauthenticated_access(client):
    """Verify that unauthenticated users are redirected or denied access across all admin routes."""
    admin_routes = [
        "/admin",
        "/admin/users",
        "/admin/documents",
        "/admin/ai-activity",
        "/admin/comparisons",
        "/admin/activity"
    ]
    for route in admin_routes:
        res = client.get(route)
        assert res.status_code in [302, 401], f"Failed unauthenticated check on {route}"

    api_routes = [
        "/api/admin/stats",
        "/api/admin/users",
        "/api/admin/documents",
        "/api/admin/ai-activity",
        "/api/admin/comparisons",
        "/api/admin/activity"
    ]
    for route in api_routes:
        res = client.get(route)
        assert res.status_code == 401, f"Failed unauthenticated API check on {route}"


def test_admin_portal_normal_user_forbidden(client):
    """Verify that authenticated normal users receive HTTP 403 Forbidden across all admin routes."""
    with client.session_transaction() as sess:
        sess["user_id"] = "regular_user@lexiguard.com"

    admin_routes = [
        "/admin",
        "/admin/users",
        "/admin/documents",
        "/admin/ai-activity",
        "/admin/comparisons",
        "/admin/activity"
    ]
    for route in admin_routes:
        res = client.get(route)
        assert res.status_code == 403, f"Failed 403 check on {route}"

    api_routes = [
        "/api/admin/stats",
        "/api/admin/users",
        "/api/admin/documents",
        "/api/admin/ai-activity",
        "/api/admin/comparisons",
        "/api/admin/activity"
    ]
    for route in api_routes:
        res = client.get(route)
        assert res.status_code == 403, f"Failed 403 API check on {route}"


def test_admin_portal_admin_user_access(client):
    """Verify that lexiguard662@gmail.com can access all admin pages and API endpoints."""
    with client.session_transaction() as sess:
        sess["user_id"] = "lexiguard662@gmail.com"

    # HTML Page Routes
    res = client.get("/admin")
    assert res.status_code == 200
    assert b"Admin Overview" in res.data
    assert b"Back to User App" in res.data

    res = client.get("/admin/users")
    assert res.status_code == 200
    assert b"Registered Accounts" in res.data

    res = client.get("/admin/documents")
    assert res.status_code == 200
    assert b"Document Repository Directory" in res.data

    res = client.get("/admin/ai-activity")
    assert res.status_code == 200
    assert b"AI Operation Activity Log" in res.data

    res = client.get("/admin/comparisons")
    assert res.status_code == 200
    assert b"Document Comparison History" in res.data

    res = client.get("/admin/activity")
    assert res.status_code == 200
    assert b"System Activity Stream" in res.data

    # API Endpoints
    res = client.get("/api/admin/users")
    assert res.status_code == 200
    users = res.get_json()
    assert isinstance(users, list)

    res = client.get("/api/admin/documents")
    assert res.status_code == 200
    docs = res.get_json()
    assert isinstance(docs, list)

    res = client.get("/api/admin/ai-activity")
    assert res.status_code == 200
    ai_act = res.get_json()
    assert isinstance(ai_act, list)

    res = client.get("/api/admin/comparisons")
    assert res.status_code == 200
    comps = res.get_json()
    assert isinstance(comps, list)

    res = client.get("/api/admin/activity")
    assert res.status_code == 200
    act = res.get_json()
    assert isinstance(act, list)
