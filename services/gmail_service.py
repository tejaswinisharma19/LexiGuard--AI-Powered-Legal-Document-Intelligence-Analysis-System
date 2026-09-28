import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import Config

logger = logging.getLogger("lexiguard")


class GmailService:
    """
    Gmail SMTP service for sending transactional email notifications (such as password reset links).
    Utilizes standard Python smtplib and MIMEText/MIMEMultipart modules with TLS encryption.
    """

    def __init__(self, server=None, port=None, username=None, password=None, use_tls=None, default_sender=None):
        self._server = server
        self._port = port
        self._username = username
        self._password = password
        self._use_tls = use_tls
        self._default_sender = default_sender

    @property
    def server(self):
        return self._server or getattr(Config, "MAIL_SERVER", None) or os.getenv("MAIL_SERVER", "smtp.gmail.com")

    @property
    def port(self):
        val = self._port if self._port is not None else (getattr(Config, "MAIL_PORT", None) or os.getenv("MAIL_PORT", 587))
        try:
            return int(val)
        except (ValueError, TypeError):
            return 587

    @property
    def username(self):
        if self._username is not None:
            return self._username
        return getattr(Config, "MAIL_USERNAME", None) or os.getenv("MAIL_USERNAME", "")

    @property
    def password(self):
        if self._password is not None:
            return self._password
        return getattr(Config, "MAIL_PASSWORD", None) or os.getenv("MAIL_PASSWORD", "")

    @property
    def use_tls(self):
        if self._use_tls is not None:
            return self._use_tls
        val = getattr(Config, "MAIL_USE_TLS", None)
        if val is None:
            val = os.getenv("MAIL_USE_TLS", "true")
        if isinstance(val, str):
            return val.lower() == "true"
        return bool(val)

    @property
    def default_sender(self):
        return (
            self._default_sender
            or getattr(Config, "MAIL_DEFAULT_SENDER", None)
            or os.getenv("MAIL_DEFAULT_SENDER", "")
            or self.username
            or "noreply@lexiguard.com"
        )

    def is_configured(self):
        """
        Check if valid SMTP username and password credentials are configured.
        """
        return bool(self.username and self.password)

    def send_password_reset_email(self, to_email, reset_url):
        """
        Send a password reset email via SMTP with HTML and plain-text fallback.
        Returns True on successful transmission, False on configuration absence or failure.
        """
        if not to_email or not reset_url:
            logger.warning("[GmailService] Missing recipient email or reset URL.")
            return False

        if not self.is_configured():
            logger.info("[GmailService] SMTP credentials not configured (MAIL_USERNAME/MAIL_PASSWORD empty). Email delivery skipped.")
            return False

        subject = "LexiGuard — Password Reset Request"

        text_content = (
            "Hello,\n\n"
            "We received a request to reset your LexiGuard password.\n\n"
            f"Reset Password Link: {reset_url}\n\n"
            "This link will expire after 1 hour.\n\n"
            "If you did not request a password reset, you can safely ignore this email.\n\n"
            "Regards,\n"
            "LexiGuard"
        )

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="font-family: Arial, sans-serif; background-color: #f4f6f8; padding: 20px; margin: 0;">
    <div style="max-width: 600px; margin: 0 auto; background: #ffffff; padding: 32px; border-radius: 8px; border: 1px solid #e2e8f0;">
        <h2 style="color: #1e293b; margin-top: 0; font-size: 20px;">LexiGuard Password Reset Request</h2>
        <p style="color: #475569; font-size: 15px; line-height: 1.5;">Hello,</p>
        <p style="color: #475569; font-size: 15px; line-height: 1.5;">We received a request to reset your LexiGuard password.</p>
        <div style="margin: 28px 0; text-align: center;">
            <a href="{reset_url}" style="background-color: #2563eb; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 15px; display: inline-block;">Reset Password</a>
        </div>
        <p style="color: #64748b; font-size: 13px; line-height: 1.5;">This link will expire after 1 hour.</p>
        <p style="color: #64748b; font-size: 13px; line-height: 1.5;">If you did not request a password reset, you can safely ignore this email.</p>
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;">
        <p style="color: #94a3b8; font-size: 12px; margin-bottom: 0;">Regards,<br><strong>LexiGuard Legal Intelligence Team</strong></p>
    </div>
</body>
</html>"""

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.default_sender
        msg["To"] = to_email

        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        try:
            with smtplib.SMTP(self.server, self.port, timeout=10) as server:
                if self.use_tls:
                    server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(msg)

            logger.info("[GmailService] Password reset email successfully sent via SMTP to recipient.")
            return True
        except smtplib.SMTPAuthenticationError as auth_err:
            logger.error("[GmailService] SMTP authentication failed: %s", str(auth_err))
            return False
        except smtplib.SMTPException as smtp_err:
            logger.error("[GmailService] SMTP protocol error: %s", str(smtp_err))
            return False
        except Exception as err:
            logger.error("[GmailService] Failed to send password reset email via SMTP: %s", str(err))
            return False
    def send_password_reset_otp_email(self, to_email, otp):
        """
        Send a 6-digit OTP code email for password reset via SMTP.
        The OTP is embedded in the email body only — never in logs, never in URLs.
        Returns True on successful SMTP submission, False otherwise.
        """
        if not to_email or not otp:
            logger.warning("[GmailService] Missing recipient email or OTP for OTP email.")
            return False

        if not self.is_configured():
            logger.info("[GmailService] SMTP credentials not configured. OTP email delivery skipped.")
            return False

        subject = "Your LexiGuard Password Reset Code"

        text_content = (
            "LexiGuard — Password Reset Verification\n\n"
            "Your verification code is:\n\n"
            f"    {otp}\n\n"
            "This code expires in 10 minutes.\n\n"
            "If you did not request a password reset, you can safely ignore this email.\n\n"
            "For your security, never share this code with anyone.\n\n"
            "— LexiGuard Legal Intelligence Platform"
        )

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;font-family:Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#F8FAFC;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#F8FAFC;padding:32px 0;">
    <tr><td align="center">
      <table width="100%" style="max-width:560px;background:#ffffff;border-radius:12px;border:1px solid #E2E8F0;overflow:hidden;">

        <!-- Header -->
        <tr><td style="background:linear-gradient(135deg,#071A35 0%,#1E3A8A 100%);padding:28px 36px;">
          <table><tr>
            <td style="width:36px;height:36px;background:rgba(255,255,255,.12);border-radius:9px;text-align:center;vertical-align:middle;">
              <span style="color:#fff;font-size:18px;font-weight:800;">L</span>
            </td>
            <td style="padding-left:12px;">
              <div style="color:#ffffff;font-size:17px;font-weight:700;letter-spacing:-.2px;">LexiGuard</div>
              <div style="color:#93C5FD;font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-top:1px;">Legal Intelligence Platform</div>
            </td>
          </tr></table>
        </td></tr>

        <!-- Body -->
        <tr><td style="padding:36px 36px 28px;">
          <h2 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0F172A;letter-spacing:-.4px;">Password Reset Verification</h2>
          <p style="margin:0 0 28px;font-size:14px;color:#475569;line-height:1.6;">
            We received a request to reset your LexiGuard password.<br>
            Enter the code below to continue.
          </p>

          <!-- OTP box -->
          <div style="background:#EFF6FF;border:1.5px solid #BFDBFE;border-radius:12px;padding:28px;text-align:center;margin-bottom:28px;">
            <div style="font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#1E40AF;margin-bottom:12px;">Your verification code</div>
            <div style="font-size:42px;font-weight:800;letter-spacing:12px;color:#1D4ED8;font-family:'Courier New',Courier,monospace;">{otp}</div>
            <div style="font-size:12px;color:#64748B;margin-top:12px;">⏱ Expires in <strong>10 minutes</strong></div>
          </div>

          <div style="background:#FFF7ED;border:1px solid #FED7AA;border-radius:8px;padding:14px 16px;margin-bottom:24px;">
            <p style="margin:0;font-size:12px;color:#92400E;line-height:1.5;">
              🔒 <strong>Security notice:</strong> Never share this code with anyone. LexiGuard staff will never ask for your verification code.
            </p>
          </div>

          <p style="margin:0;font-size:13px;color:#94A3B8;line-height:1.6;">
            If you did not request a password reset, you can safely ignore this email. Your account remains secure.
          </p>
        </td></tr>

        <!-- Footer -->
        <tr><td style="padding:20px 36px;border-top:1px solid #E2E8F0;background:#F8FAFC;">
          <p style="margin:0;font-size:11px;color:#94A3B8;text-align:center;">
            &copy; LexiGuard AI Legal Intelligence Systems &nbsp;|&nbsp; Confidential &amp; Secure
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.default_sender
        msg["To"] = to_email

        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        try:
            with smtplib.SMTP(self.server, self.port, timeout=15) as smtp_conn:
                if self.use_tls:
                    smtp_conn.starttls()
                if self.username and self.password:
                    smtp_conn.login(self.username, self.password)
                smtp_conn.send_message(msg)

            logger.info("[GmailService] Password reset OTP email sent successfully.")
            return True
        except smtplib.SMTPAuthenticationError:
            logger.error("[GmailService] SMTP authentication failed sending OTP email.")
            return False
        except smtplib.SMTPException as smtp_err:
            logger.error("[GmailService] SMTP error sending OTP email: %s", type(smtp_err).__name__)
            return False
        except Exception as err:
            logger.error("[GmailService] Unexpected error sending OTP email: %s", type(err).__name__)
            return False
