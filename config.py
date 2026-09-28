import os

from dotenv import load_dotenv


load_dotenv(override=True)

INSECURE_SECRET_KEYS = {
    "dev-secret-key-change-in-production",
    "lexiguard-development-key",
    "lexiguard-dev-secret-key-do-not-use-in-production",
    "secret",
    "secret_key",
    "change-me",
    "changeme",
    "123456",
}


def get_secret_key():
    env = os.getenv("FLASK_ENV", os.getenv("ENV", "development")).lower()
    raw_secret = os.getenv("SECRET_KEY")

    if env == "production":
        if not raw_secret or raw_secret.strip() in INSECURE_SECRET_KEYS:
            raise ValueError("SECRET_KEY must be securely and explicitly configured in production environment.")
        return raw_secret
    return raw_secret if raw_secret else "lexiguard-dev-secret-key-do-not-use-in-production"


class Config:
    SECRET_KEY = get_secret_key()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

    AWS_REGION = os.getenv("AWS_REGION")

    # PostgreSQL Configuration
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB = os.getenv("POSTGRES_DB", "lexiguard_db")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

    # SMTP Mail Server Configuration
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "")

    SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN", "")
    ENABLE_SNS_NOTIFICATIONS = os.getenv("ENABLE_SNS_NOTIFICATIONS", "false").lower() == "true"

