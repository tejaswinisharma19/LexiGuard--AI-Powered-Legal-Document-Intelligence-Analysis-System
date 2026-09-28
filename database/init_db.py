import os
import sys
import logging
from datetime import datetime, timezone

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import Config
import psycopg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("init_db")


def get_postgres_connection(dbname=None, autocommit=False):
    """
    Establish a connection to PostgreSQL using settings from Config.
    """
    target_db = dbname or Config.POSTGRES_DB
    return psycopg.connect(
        host=Config.POSTGRES_HOST,
        port=Config.POSTGRES_PORT,
        user=Config.POSTGRES_USER,
        password=Config.POSTGRES_PASSWORD,
        dbname=target_db,
        autocommit=autocommit
    )


def ensure_database_exists():
    """
    Connect to the default 'postgres' database and verify that Config.POSTGRES_DB exists.
    If not, create it.
    """
    logger.info("Checking if database '%s' exists...", Config.POSTGRES_DB)
    with get_postgres_connection(dbname="postgres", autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (Config.POSTGRES_DB,))
            exists = cur.fetchone()
            if not exists:
                logger.info("Database '%s' does not exist. Creating...", Config.POSTGRES_DB)
                # SQL identifier formatting for database name
                cur.execute(f'CREATE DATABASE "{Config.POSTGRES_DB}"')
                logger.info("Database '%s' created successfully.", Config.POSTGRES_DB)
            else:
                logger.info("Database '%s' already exists.", Config.POSTGRES_DB)


def init_schema():
    """
    Create the 'users' and 'documents' tables, indexes, and seed the default admin account.
    """
    logger.info("Initializing schema in '%s'...", Config.POSTGRES_DB)
    with get_postgres_connection(autocommit=True) as conn:
        with conn.cursor() as cur:
            # Users table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    full_name TEXT,
                    created_at TEXT,
                    role TEXT DEFAULT 'user',
                    status TEXT DEFAULT 'active',
                    reset_otp_hash TEXT,
                    reset_otp_expires TEXT,
                    reset_otp_attempts INTEGER DEFAULT 0,
                    reset_otp_verified BOOLEAN DEFAULT FALSE,
                    reset_otp_authorized BOOLEAN DEFAULT FALSE,
                    reset_otp_auth_expires TEXT,
                    reset_otp_resend_at TEXT,
                    reset_token TEXT,
                    reset_token_used BOOLEAN DEFAULT FALSE
                );
            """)
            logger.info("Table 'users' verified/created.")

            # Documents table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    filename TEXT,
                    created_at TEXT,
                    upload_date TEXT,
                    file_path TEXT,
                    data JSONB NOT NULL DEFAULT '{}'::jsonb
                );
            """)
            logger.info("Table 'documents' verified/created.")

            # Index on documents(user_id)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
            """)
            logger.info("Index 'idx_documents_user_id' verified/created.")

            # Ensure administrator account exists
            admin_email = "lexiguard662@gmail.com"
            cur.execute("SELECT email, role FROM users WHERE email = %s", (admin_email,))
            existing_admin = cur.fetchone()

            if not existing_admin:
                now_iso = datetime.now(timezone.utc).isoformat()
                # Use a dummy initial password hash if fresh; admin sets via OTP reset or direct setup
                # werkzeug format dummy hash that will not match any random password
                initial_hash = "scram-sha-256$unset$placeholder_admin_hash"
                cur.execute("""
                    INSERT INTO users (email, password_hash, full_name, created_at, role, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (admin_email, initial_hash, "TEJASWINI SHARMA", now_iso, "admin", "active"))
                logger.info("Default administrator account seeded: %s (role=admin, status=active)", admin_email)
            else:
                # Ensure role is admin and status is active
                cur.execute("""
                    UPDATE users SET role = 'admin', status = 'active' WHERE email = %s
                """, (admin_email,))
                logger.info("Administrator account verified: %s (role=admin, status=active)", admin_email)

    logger.info("Database schema initialization complete.")


def run():
    ensure_database_exists()
    init_schema()


if __name__ == "__main__":
    run()
