from flask import Blueprint, render_template, session

from extensions import login_required, postgresql_service

analysis_bp = Blueprint("analysis", __name__)


@analysis_bp.route("/analysis", endpoint="analyze_page")
@analysis_bp.route("/analyze", endpoint="analyze_page_alt")
@login_required
def analyze_page():
    """
    Render AI analysis and Q&A workspace page.
    """
    return render_template(
        "analyze.html",
        user_name=session.get("user_name", "User"),
        user_id=session.get("user_id", ""),
        is_constitution_mode=False
    )


@analysis_bp.route("/constitution", endpoint="constitution_page")
@login_required
def constitution_page():
    """
    Render Constitution of India Q&A legal research workspace page.
    """
    return render_template(
        "analyze.html",
        user_name=session.get("user_name", "User"),
        user_id=session.get("user_id", ""),
        is_constitution_mode=True
    )


@analysis_bp.route("/compare", endpoint="compare_page")
@login_required
def compare_page():
    """
    Render the document comparison page.
    """
    return render_template(
        "compare.html",
        user_name=session.get("user_name", "User"),
        user_id=session.get("user_id", "")
    )


@analysis_bp.route("/history", endpoint="history_page")
@login_required
def history_page():
    """
    Render the analysis history page.
    """
    return render_template(
        "history.html",
        user_name=session.get("user_name", "User"),
        user_id=session.get("user_id", "")
    )


@analysis_bp.route("/chat-history", endpoint="chat_history_page")
@login_required
def chat_history_page():
    """
    Render the chat history page.
    """
    return render_template(
        "chat_history.html",
        user_name=session.get("user_name", "User"),
        user_id=session.get("user_id", "")
    )


@analysis_bp.route("/comparison-history", endpoint="comparison_history_page")
@login_required
def comparison_history_page():
    """
    Render the comparison history page.
    """
    return render_template(
        "comparison_history.html",
        user_name=session.get("user_name", "User"),
        user_id=session.get("user_id", "")
    )


@analysis_bp.route("/profile", endpoint="profile")
@analysis_bp.route("/profile", endpoint="profile_page")
@login_required
def profile_page():
    """
    Render user profile page.
    """
    current_user_email = session.get("user_id", "")
    try:
        user_record = postgresql_service.get_user_by_email(current_user_email) or {}
    except Exception:
        user_record = {}

    try:
        user_stats = postgresql_service.get_user_stats(current_user_email)
    except Exception:
        user_stats = {}

    return render_template(
        "profile.html",
        user_name=session.get("user_name", "User"),
        user_id=current_user_email,
        email=current_user_email,
        created_at=user_record.get("created_at", ""),
        is_admin=session.get("is_admin", False),
        user_stats=user_stats
    )



@analysis_bp.route("/settings", endpoint="settings")
@analysis_bp.route("/settings", endpoint="settings_page")
@login_required
def settings_page():
    """
    Render application settings page.
    """
    return render_template(
        "settings.html",
        user_name=session.get("user_name", "User"),
        user_id=session.get("user_id", ""),
        is_admin=session.get("is_admin", False)
    )
