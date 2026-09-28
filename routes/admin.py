import logging

from flask import Blueprint, jsonify, render_template, session

from extensions import admin_required, postgresql_service

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin", methods=["GET"], endpoint="admin_page")
@admin_required
def admin_page():
    """Render Admin Overview page."""
    return render_template(
        "admin/overview.html",
        active_page="overview",
        user_name=session.get("user_name", "Admin"),
        user_id=session.get("user_id", "")
    )


@admin_bp.route("/admin/users", methods=["GET"], endpoint="admin_users_page")
@admin_required
def admin_users_page():
    """Render Admin Users directory page."""
    return render_template(
        "admin/users.html",
        active_page="users",
        user_name=session.get("user_name", "Admin"),
        user_id=session.get("user_id", "")
    )


@admin_bp.route("/admin/documents", methods=["GET"], endpoint="admin_documents_page")
@admin_required
def admin_documents_page():
    """Render Admin Documents directory page."""
    return render_template(
        "admin/documents.html",
        active_page="documents",
        user_name=session.get("user_name", "Admin"),
        user_id=session.get("user_id", "")
    )


@admin_bp.route("/admin/ai-activity", methods=["GET"], endpoint="admin_ai_activity_page")
@admin_required
def admin_ai_activity_page():
    """Render Admin AI Activity monitoring page."""
    return render_template(
        "admin/ai_activity.html",
        active_page="ai-activity",
        user_name=session.get("user_name", "Admin"),
        user_id=session.get("user_id", "")
    )


@admin_bp.route("/admin/comparisons", methods=["GET"], endpoint="admin_comparisons_page")
@admin_required
def admin_comparisons_page():
    """Render Admin Comparisons history page."""
    return render_template(
        "admin/comparisons.html",
        active_page="comparisons",
        user_name=session.get("user_name", "Admin"),
        user_id=session.get("user_id", "")
    )


@admin_bp.route("/admin/activity", methods=["GET"], endpoint="admin_activity_page")
@admin_required
def admin_activity_page():
    """Render Admin System Activity stream page."""
    return render_template(
        "admin/activity.html",
        active_page="activity",
        user_name=session.get("user_name", "Admin"),
        user_id=session.get("user_id", "")
    )


# ==========================================
# Admin API Endpoints
# ==========================================

@admin_bp.route("/api/admin/stats", methods=["GET"], endpoint="admin_stats_api")
@admin_required
def admin_stats_api():
    """Return system-wide statistics for the Admin Dashboard."""
    try:
        stats = postgresql_service.get_system_stats()
        return jsonify(stats), 200
    except Exception as error:
        logging.exception("Error in admin_stats_api: %s", error)
        return jsonify({
            "error": "Unable to fetch system statistics."
        }), 500


@admin_bp.route("/api/admin/users", methods=["GET"], endpoint="admin_users_api")
@admin_required
def admin_users_api():
    """Return user accounts list for admin overview (no password hashes)."""
    try:
        users = postgresql_service.get_all_users_admin()
        return jsonify(users), 200
    except Exception as error:
        logging.exception("Error in admin_users_api: %s", error)
        return jsonify({
            "error": "Unable to fetch user directory."
        }), 500


@admin_bp.route("/api/admin/documents", methods=["GET"], endpoint="admin_documents_api")
@admin_required
def admin_documents_api():
    """Return document directory for admin overview."""
    try:
        docs = postgresql_service.get_all_documents_admin()
        return jsonify(docs), 200
    except Exception as error:
        logging.exception("Error in admin_documents_api: %s", error)
        return jsonify({
            "error": "Unable to fetch document directory."
        }), 500


@admin_bp.route("/api/admin/ai-activity", methods=["GET"], endpoint="admin_ai_activity_api")
@admin_required
def admin_ai_activity_api():
    """Return AI operations activity log for admin monitoring."""
    try:
        activity = postgresql_service.get_ai_activity_admin()
        return jsonify(activity), 200
    except Exception as error:
        logging.exception("Error in admin_ai_activity_api: %s", error)
        return jsonify({
            "error": "Unable to fetch AI activity log."
        }), 500


@admin_bp.route("/api/admin/comparisons", methods=["GET"], endpoint="admin_comparisons_api")
@admin_required
def admin_comparisons_api():
    """Return comparison operations log for admin monitoring."""
    try:
        comparisons = postgresql_service.get_comparison_activity_admin()
        return jsonify(comparisons), 200
    except Exception as error:
        logging.exception("Error in admin_comparisons_api: %s", error)
        return jsonify({
            "error": "Unable to fetch comparison activity log."
        }), 500


@admin_bp.route("/api/admin/activity", methods=["GET"], endpoint="admin_activity_api")
@admin_required
def admin_activity_api():
    """Return full system activity stream for admin monitoring."""
    try:
        stats = postgresql_service.get_system_stats()
        return jsonify(stats.get("recent_activity", [])), 200
    except Exception as error:
        logging.exception("Error in admin_activity_api: %s", error)
        return jsonify({
            "error": "Unable to fetch system activity stream."
        }), 500
