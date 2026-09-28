from functools import wraps
from flask import jsonify, redirect, request, session, url_for
from services.postgresql_service import PostgreSQLService
from services.local_storage_service import LocalStorageService
from aws.ses_service import SESService
from aws.sns_service import SNSService
from services.gmail_service import GmailService
from config import Config

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf"}

postgresql_service = PostgreSQLService()
local_storage_service = LocalStorageService(upload_folder=UPLOAD_FOLDER)
dynamodb_service = postgresql_service
s3_service = local_storage_service
ses_service = SESService()
sns_service = SNSService()
gmail_service = GmailService()



def login_required(f):
    """
    Decorator to ensure user is logged in.
    Redirects HTML requests to /login and returns JSON 401 for API routes.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            if request.path.startswith("/api/"):
                return jsonify({
                    "error": "Authentication required. Please log in."
                }), 401
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """
    Decorator enforcing server-side admin authorization.
    Verifies current user identity directly via database / email rule.
    Returns 401 for unauthenticated users, 403 Forbidden for non-admins.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            if request.path.startswith("/api/"):
                return jsonify({
                    "error": "Authentication required. Please log in."
                }), 401
            return redirect(url_for("auth.login", next=request.url))

        email_clean = user_id.lower().strip()
        user_rec = dynamodb_service.get_user_by_email(email_clean)

        is_admin = bool(user_rec and user_rec.get("role") == "admin")

        if not is_admin:
            if request.path.startswith("/api/"):
                return jsonify({
                    "error": "Forbidden: Admin privileges required."
                }), 403
            return jsonify({
                "error": "Forbidden: Admin privileges required."
            }), 403

        return f(*args, **kwargs)

    return decorated_function


def allowed_file(filename):
    """
    Check whether the uploaded file has an allowed file extension.
    """
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def build_document_context(chunks, document_label):
    """
    Build structured context from document chunks for AI comparison.
    """
    context_parts = []
    for chunk in chunks:
        context_parts.append(
            f"--- {document_label} | "
            f"Page {chunk['page_number']} | "
            f"Chunk {chunk['chunk_number']} ---\n"
            f"{chunk['text']}"
        )
    return "\n\n".join(context_parts)
