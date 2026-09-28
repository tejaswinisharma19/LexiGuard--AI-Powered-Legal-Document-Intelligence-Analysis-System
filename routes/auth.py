import hashlib
import logging
import secrets
import re
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import gmail_service, login_required, postgresql_service

logger = logging.getLogger("lexiguard")

auth_bp = Blueprint("auth", __name__)

# ---------------------------------------------------------------------------
# OTP constants
# ---------------------------------------------------------------------------
OTP_EXPIRY_MINUTES = 10
OTP_MAX_ATTEMPTS = 5
OTP_RESET_AUTH_MINUTES = 10   # window after OTP verification to submit new password
OTP_RESEND_COOLDOWN_SECONDS = 60


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mask_email(email: str) -> str:
    """Return masked email, e.g. w***@gmail.com"""
    try:
        local, domain = email.split("@", 1)
        if len(local) <= 1:
            return f"*@{domain}"
        return f"{local[0]}***@{domain}"
    except Exception:
        return "***"


def _generate_otp() -> str:
    """Generate a cryptographically secure 6-digit numeric OTP."""
    return str(secrets.randbelow(900000) + 100000)   # guaranteed 6 digits


def _hash_otp(otp: str) -> str:
    """Return SHA-256 hex digest of the OTP string."""
    return hashlib.sha256(otp.encode("utf-8")).hexdigest()


def _is_valid_email(email: str) -> bool:
    pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    return bool(pattern.match(email))


# ---------------------------------------------------------------------------
# Dashboard / home
# ---------------------------------------------------------------------------

@auth_bp.route("/", endpoint="home")
@auth_bp.route("/dashboard", endpoint="dashboard")
@login_required
def home():
    """Render the main dashboard overview page."""
    return render_template(
        "dashboard.html",
        user_name=session.get("user_name", "User"),
        user_id=session.get("user_id", "")
    )


# ---------------------------------------------------------------------------
# Login / Register / Logout
# ---------------------------------------------------------------------------

@auth_bp.route("/login", methods=["GET", "POST"], endpoint="login")
def login():
    """Render login page or process user login."""
    error = None
    message = request.args.get("message")

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            error = "Email and password are required."
        else:
            user = postgresql_service.get_user_by_email(email)

            if not user or not check_password_hash(user["password_hash"], password):
                error = "Invalid email address or password."
            else:
                session.clear()
                session["user_id"] = user["email"]
                session["user_name"] = user.get("full_name") or user["email"]
                session["is_admin"] = bool(user.get("role") == "admin")

                next_url = request.args.get("next")
                if next_url and next_url.startswith("/"):
                    return redirect(next_url)
                return redirect(url_for("auth.home"))

    return render_template("login.html", error=error, message=message)


@auth_bp.route("/register", methods=["GET", "POST"], endpoint="register")
def register():
    """Render registration page or create new user account."""
    error = None

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not full_name or not email or not password:
            error = "All fields are required."
        elif len(password) < 6:
            error = "Password must be at least 6 characters long."
        elif password != confirm_password:
            error = "Passwords do not match."
        else:
            existing_user = postgresql_service.get_user_by_email(email)
            if existing_user:
                error = "An account with this email address already exists."
            else:
                hashed_password = generate_password_hash(password)
                user_data = {
                    "email": email,
                    "password_hash": hashed_password,
                    "full_name": full_name,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                postgresql_service.save_user(user_data)

                session.clear()
                session["user_id"] = email
                session["user_name"] = full_name
                session["is_admin"] = False
                return redirect(url_for("auth.home"))

    return render_template("register.html", error=error)


@auth_bp.route("/logout", methods=["GET", "POST"], endpoint="logout")
def logout():
    """Log out user by clearing Flask session."""
    session.clear()
    if request.path.startswith("/api/"):
        return jsonify({"message": "Logged out successfully."})
    return redirect(url_for("auth.login"))


# ---------------------------------------------------------------------------
# STEP 1 — Forgot Password (email entry)
# ---------------------------------------------------------------------------

@auth_bp.route("/forgot-password", methods=["GET"], endpoint="forgot_password")
def forgot_password():
    """Render the forgot-password email entry page."""
    return render_template("forgot_password.html")


# ---------------------------------------------------------------------------
# STEP 2 — Send OTP API endpoint
# ---------------------------------------------------------------------------

@auth_bp.route("/api/auth/send-otp", methods=["POST"], endpoint="send_otp")
def send_otp():
    """
    Generate a secure 6-digit OTP, hash it, store in DB, and send via Gmail.
    Generic response regardless of whether the email exists (prevents enumeration).
    Rate-limited by resend cooldown stored server-side.
    """
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()

    if not email or not _is_valid_email(email):
        return jsonify({"ok": False, "error": "Please enter a valid email address."}), 400

    generic_ok = jsonify({
        "ok": True,
        "message": "If an account exists for this email address, a verification code has been sent.",
        "masked_email": _mask_email(email)
    })

    user = postgresql_service.get_user_by_email(email)
    if not user:
        # No account — return generic success to prevent enumeration
        logger.info("[OTP] Forgot-password requested for non-existent email.")
        return generic_ok

    # Enforce resend cooldown ONLY when a previously issued OTP is still active.
    # If the stored OTP has already expired (> OTP_EXPIRY_MINUTES old) it is
    # worthless, and a fresh send attempt must be allowed immediately.
    otp_expires_str = user.get("reset_otp_expires", "")
    if otp_expires_str:
        try:
            otp_expires = datetime.fromisoformat(otp_expires_str)
            now = datetime.now(timezone.utc)

            # Only apply cooldown when the OTP is still within its validity window
            if now < otp_expires:
                last_sent = otp_expires - timedelta(minutes=OTP_EXPIRY_MINUTES)
                seconds_since_sent = (now - last_sent).total_seconds()
                if 0 < seconds_since_sent < OTP_RESEND_COOLDOWN_SECONDS:
                    remaining = int(OTP_RESEND_COOLDOWN_SECONDS - seconds_since_sent)
                    # Return a helper response so the frontend can guide the user to
                    # /verify-otp where the already-sent code can be entered, rather
                    # than just showing an opaque "please wait" error.
                    return jsonify({
                        "ok": False,
                        "has_active_otp": True,
                        "cooldown": remaining,
                        "masked_email": _mask_email(email),
                        "verify_url": url_for("auth.verify_otp_page", email=email),
                        "error": (
                            f"A verification code was recently sent to {_mask_email(email)}. "
                            f"Please check your inbox, or wait {remaining} seconds to request a new one."
                        )
                    }), 429
            # OTP is expired — fall through and issue a fresh one
        except Exception:
            pass

    # Generate OTP (not yet stored — store only after successful send)
    raw_otp = _generate_otp()
    otp_hash = _hash_otp(raw_otp)
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES)).isoformat()

    # Pre-check: if SMTP is not even configured, fail fast without touching the DB.
    # This prevents storing an OTP that will never reach the user.
    if not gmail_service.is_configured():
        logger.error(
            "[OTP] Cannot send OTP — SMTP credentials (MAIL_USERNAME / MAIL_PASSWORD) "
            "are not configured in the environment. Set them in .env and restart the server."
        )
        return jsonify({
            "ok": False,
            "error": "Email delivery is not available right now. Please contact support."
        }), 503

    # Store OTP first (so the DB is consistent if the SMTP call blocks then disconnects)
    postgresql_service.save_otp(email, otp_hash, expires_at)

    # Attempt SMTP delivery — OTP is passed only to the email service, never to the browser
    sent = gmail_service.send_password_reset_otp_email(email, raw_otp)
    if not sent:
        # SMTP failed after the OTP was stored.
        # Invalidate it immediately so the DB does not hold an active-but-undelivered record.
        # Without this, the next request within 60 s would show the cooldown message while
        # directing the user to check an inbox that received nothing.
        postgresql_service.invalidate_otp(email)
        logger.warning("[OTP] OTP invalidated after failed SMTP delivery.")
        return jsonify({
            "ok": False,
            "error": "Unable to send the verification code right now. Please try again later."
        }), 503

    logger.info("[OTP] Password reset OTP stored and delivered successfully.")
    return generic_ok



# ---------------------------------------------------------------------------
# STEP 2b — Resend OTP
# ---------------------------------------------------------------------------

@auth_bp.route("/api/auth/resend-otp", methods=["POST"], endpoint="resend_otp")
def resend_otp():
    """
    Resend the OTP. Invalidates previous OTP, enforces cooldown.
    Delegates directly to send_otp logic.
    """
    # Reuse the same send_otp logic by forwarding the request data
    return send_otp()


# ---------------------------------------------------------------------------
# STEP 2 page — Verify OTP
# ---------------------------------------------------------------------------

@auth_bp.route("/verify-otp", methods=["GET"], endpoint="verify_otp_page")
def verify_otp_page():
    """Render the OTP entry page. Email passed via query param (masked on server)."""
    email = request.args.get("email", "").strip().lower()
    if not email or not _is_valid_email(email):
        return redirect(url_for("auth.forgot_password"))
    return render_template("verify_otp.html", masked_email=_mask_email(email), email=email)


# ---------------------------------------------------------------------------
# STEP 3 — Verify OTP API endpoint
# ---------------------------------------------------------------------------

@auth_bp.route("/api/auth/verify-otp", methods=["POST"], endpoint="verify_otp")
def verify_otp():
    """
    Verify submitted OTP against stored hash.
    On success: mark OTP as verified, create server-side reset authorization.
    On failure: increment attempt counter; lock after MAX_ATTEMPTS.
    """
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    submitted_otp = str(data.get("otp", "")).strip()

    if not email or not submitted_otp:
        return jsonify({"ok": False, "error": "Email and verification code are required."}), 400

    user = postgresql_service.get_user_by_email(email)
    if not user:
        return jsonify({"ok": False, "error": "Invalid request."}), 400

    # Check OTP exists
    stored_hash = user.get("reset_otp_hash")
    if not stored_hash:
        return jsonify({"ok": False, "error": "No verification code found. Please request a new code."}), 400

    # Check expiration
    expires_str = user.get("reset_otp_expires", "")
    if expires_str:
        try:
            expires_at = datetime.fromisoformat(expires_str)
            if datetime.now(timezone.utc) > expires_at:
                postgresql_service.invalidate_otp(email)
                return jsonify({"ok": False, "error": "Your verification code has expired. Please request a new code."}), 400
        except Exception:
            pass

    # Check attempt count
    attempts = int(user.get("reset_otp_attempts", 0))
    if attempts >= OTP_MAX_ATTEMPTS:
        postgresql_service.invalidate_otp(email)
        return jsonify({"ok": False, "error": "Too many incorrect attempts. Please request a new code."}), 429

    # Verify OTP hash
    submitted_hash = _hash_otp(submitted_otp)
    if submitted_hash != stored_hash:
        postgresql_service.increment_otp_attempts(email)
        remaining = OTP_MAX_ATTEMPTS - (attempts + 1)
        msg = "Incorrect verification code. Please try again."
        if remaining <= 0:
            postgresql_service.invalidate_otp(email)
            msg = "Too many incorrect attempts. Please request a new code."
        return jsonify({"ok": False, "error": msg, "remaining_attempts": max(0, remaining)}), 400

    # OTP is correct — create server-side reset authorization
    auth_expires = (datetime.now(timezone.utc) + timedelta(minutes=OTP_RESET_AUTH_MINUTES)).isoformat()
    postgresql_service.mark_otp_verified(email, auth_expires)

    # Store authorization in Flask session (server-side; user cannot forge)
    session["otp_reset_email"] = email
    session["otp_reset_authorized"] = True
    session["otp_reset_auth_expires"] = auth_expires

    logger.info("[OTP] OTP verified successfully.")
    return jsonify({"ok": True, "redirect": url_for("auth.reset_password_otp")})


# ---------------------------------------------------------------------------
# STEP 3 page — Set new password
# ---------------------------------------------------------------------------

@auth_bp.route("/reset-password", methods=["GET"], endpoint="reset_password_otp")
def reset_password_otp():
    """
    Render the set-new-password page.
    Only accessible if server-side OTP authorization is active and unexpired.
    """
    # Validate session-side authorization
    if not session.get("otp_reset_authorized") or not session.get("otp_reset_email"):
        return redirect(url_for("auth.forgot_password"))

    auth_expires_str = session.get("otp_reset_auth_expires", "")
    if auth_expires_str:
        try:
            auth_expires = datetime.fromisoformat(auth_expires_str)
            if datetime.now(timezone.utc) > auth_expires:
                session.pop("otp_reset_authorized", None)
                session.pop("otp_reset_email", None)
                session.pop("otp_reset_auth_expires", None)
                return redirect(url_for("auth.forgot_password"))
        except Exception:
            pass

    # Also double-check DB authorization (cannot be forged by client)
    email = session["otp_reset_email"]
    user = postgresql_service.get_user_by_email(email)
    if not user or not user.get("reset_otp_authorized"):
        session.pop("otp_reset_authorized", None)
        return redirect(url_for("auth.forgot_password"))

    return render_template("reset_password.html")


# ---------------------------------------------------------------------------
# STEP 4 — Update password API endpoint
# ---------------------------------------------------------------------------

@auth_bp.route("/api/auth/reset-password", methods=["POST"], endpoint="do_reset_password")
def do_reset_password():
    """
    Update user password after verified OTP authorization.
    Authorization determined entirely server-side — no client flag trusted.
    """
    # Validate session-side authorization
    if not session.get("otp_reset_authorized") or not session.get("otp_reset_email"):
        return jsonify({"ok": False, "error": "Unauthorized. Please complete the verification process."}), 401

    auth_expires_str = session.get("otp_reset_auth_expires", "")
    if auth_expires_str:
        try:
            auth_expires = datetime.fromisoformat(auth_expires_str)
            if datetime.now(timezone.utc) > auth_expires:
                session.pop("otp_reset_authorized", None)
                session.pop("otp_reset_email", None)
                session.pop("otp_reset_auth_expires", None)
                return jsonify({"ok": False, "error": "Authorization expired. Please start the process again."}), 401
        except Exception:
            pass

    email = session["otp_reset_email"]

    # Double-check DB authorization
    user = postgresql_service.get_user_by_email(email)
    if not user or not user.get("reset_otp_authorized"):
        session.pop("otp_reset_authorized", None)
        return jsonify({"ok": False, "error": "Unauthorized. Please complete verification."}), 401

    data = request.get_json(silent=True) or {}
    password = data.get("password", "").strip()
    confirm_password = data.get("confirm_password", "").strip()

    if not password or len(password) < 6:
        return jsonify({"ok": False, "error": "Password must be at least 6 characters long."}), 400
    if password != confirm_password:
        return jsonify({"ok": False, "error": "Passwords do not match."}), 400

    # Update password using existing hashing mechanism
    new_hash = generate_password_hash(password)
    postgresql_service.update_user_password(email, new_hash)

    # Invalidate all OTP and reset authorization state
    postgresql_service.invalidate_otp(email)
    session.pop("otp_reset_authorized", None)
    session.pop("otp_reset_email", None)
    session.pop("otp_reset_auth_expires", None)

    logger.info("[OTP] Password reset completed successfully.")
    return jsonify({"ok": True, "message": "Your password has been updated successfully."})
