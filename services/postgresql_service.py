import json
import logging
from datetime import datetime, timezone
import psycopg
from psycopg.rows import dict_row

from config import Config

logger = logging.getLogger("lexiguard")


class PostgreSQLService:
    """
    PostgreSQL service replacing AWS DynamoDB for LexiGuard.
    Provides complete storage operations for users, documents, histories,
    and admin metrics using parameterized queries and JSONB.
    """

    def __init__(
        self,
        host=None,
        port=None,
        dbname=None,
        user=None,
        password=None
    ):
        self.host = host or Config.POSTGRES_HOST
        self.port = port or Config.POSTGRES_PORT
        self.dbname = dbname or Config.POSTGRES_DB
        self.user = user or Config.POSTGRES_USER
        self.password = password or Config.POSTGRES_PASSWORD

    def _get_connection(self):
        """Create and return an autocommit connection with dictionary row factory."""
        return psycopg.connect(
            host=self.host,
            port=self.port,
            dbname=self.dbname,
            user=self.user,
            password=self.password,
            autocommit=True,
            row_factory=dict_row
        )

    # -------------------------------------------------------------------------
    # USER OPERATIONS
    # -------------------------------------------------------------------------

    def save_user(self, user_data):
        """
        Save or update user account details.
        Returns user dictionary for interface compatibility.
        """
        email = user_data["email"].lower().strip()
        password_hash = user_data["password_hash"]
        full_name = user_data.get("full_name", "")
        created_at = user_data.get("created_at") or datetime.now(timezone.utc).isoformat()
        role = user_data.get("role", "user")
        status = user_data.get("status", "active")

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (email, password_hash, full_name, created_at, role, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (email) DO UPDATE SET
                        password_hash = EXCLUDED.password_hash,
                        full_name = CASE WHEN EXCLUDED.full_name <> '' THEN EXCLUDED.full_name ELSE users.full_name END,
                        role = EXCLUDED.role,
                        status = EXCLUDED.status;
                """, (email, password_hash, full_name, created_at, role, status))

        return {
            "document_id": f"USER#{email}",
            "email": email,
            "password_hash": password_hash,
            "full_name": full_name,
            "created_at": created_at,
            "role": role,
            "status": status
        }

    def delete_user(self, email):
        """
        Delete a user record by email.
        """
        if not email:
            return False
        email_clean = str(email).replace("USER#", "").lower().strip()
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM users WHERE email = %s;", (email_clean,))
        return True

    def get_user_by_email(self, email):
        """
        Retrieve user account details by email.
        Returns a dictionary compatible with DynamoDB format, or None if not found.
        """
        if not email:
            return None
        email_clean = str(email).replace("USER#", "").lower().strip()

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT email, password_hash, full_name, created_at, role, status,
                           reset_otp_hash, reset_otp_expires, reset_otp_attempts,
                           reset_otp_verified, reset_otp_authorized, reset_otp_auth_expires,
                           reset_otp_resend_at, reset_token, reset_token_used
                    FROM users WHERE email = %s;
                """, (email_clean,))
                row = cur.fetchone()
                if not row:
                    return None

                item = dict(row)
                item["document_id"] = f"USER#{email_clean}"
                # Ensure boolean/string defaults match existing logic
                item["reset_otp_attempts"] = int(item.get("reset_otp_attempts") or 0)
                item["reset_otp_verified"] = bool(item.get("reset_otp_verified"))
                item["reset_otp_authorized"] = bool(item.get("reset_otp_authorized"))
                item["reset_otp_auth_expires"] = item.get("reset_otp_auth_expires") or ""
                return item

    def save_otp(self, email, otp_hash, expires_at):
        """
        Save OTP hash and expiration for password reset flow.
        """
        email_clean = str(email).replace("USER#", "").lower().strip()
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users SET
                        reset_otp_hash = %s,
                        reset_otp_expires = %s,
                        reset_otp_attempts = 0,
                        reset_otp_verified = FALSE,
                        reset_otp_authorized = FALSE,
                        reset_otp_auth_expires = '',
                        reset_otp_resend_at = %s
                    WHERE email = %s;
                """, (otp_hash, expires_at, expires_at, email_clean))

    def increment_otp_attempts(self, email):
        """
        Atomically increment failed OTP attempt counter.
        """
        email_clean = str(email).replace("USER#", "").lower().strip()
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users SET
                        reset_otp_attempts = COALESCE(reset_otp_attempts, 0) + 1
                    WHERE email = %s;
                """, (email_clean,))

    def mark_otp_verified(self, email, auth_expires_at):
        """
        Mark OTP as verified and store password reset authorization expiry.
        """
        email_clean = str(email).replace("USER#", "").lower().strip()
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users SET
                        reset_otp_verified = TRUE,
                        reset_otp_authorized = TRUE,
                        reset_otp_auth_expires = %s
                    WHERE email = %s;
                """, (auth_expires_at, email_clean))

    def invalidate_otp(self, email):
        """
        Fully clear OTP and reset-authorization state.
        """
        email_clean = str(email).replace("USER#", "").lower().strip()
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users SET
                        reset_otp_hash = NULL,
                        reset_otp_expires = NULL,
                        reset_otp_attempts = 0,
                        reset_otp_verified = FALSE,
                        reset_otp_authorized = FALSE,
                        reset_otp_auth_expires = ''
                    WHERE email = %s;
                """, (email_clean,))

    def update_user_password(self, email, new_password_hash):
        """
        Update user password hash and clear all OTP state.
        """
        email_clean = str(email).replace("USER#", "").lower().strip()
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users SET
                        password_hash = %s,
                        reset_otp_hash = NULL,
                        reset_otp_expires = NULL,
                        reset_otp_attempts = 0,
                        reset_otp_verified = FALSE,
                        reset_otp_authorized = FALSE,
                        reset_otp_auth_expires = '',
                        reset_token = NULL,
                        reset_token_used = FALSE
                    WHERE email = %s;
                """, (new_password_hash, email_clean))

    # -------------------------------------------------------------------------
    # DOCUMENT OPERATIONS
    # -------------------------------------------------------------------------

    def save_document(self, document):
        """
        Save document metadata and JSON payload to PostgreSQL.
        """
        doc_id = document.get("document_id")
        user_id = str(document.get("user_id", "")).replace("USER#", "").lower().strip()
        filename = document.get("filename", "")
        created_at = document.get("created_at") or document.get("upload_date") or datetime.now(timezone.utc).isoformat()
        upload_date = document.get("upload_date") or created_at
        file_path = document.get("file_path") or document.get("s3_object_key", "")

        # Store complete document dict inside JSONB data payload
        payload_json = json.dumps(document)

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO documents (document_id, user_id, filename, created_at, upload_date, file_path, data)
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                    ON CONFLICT (document_id) DO UPDATE SET
                        user_id = EXCLUDED.user_id,
                        filename = EXCLUDED.filename,
                        created_at = EXCLUDED.created_at,
                        upload_date = EXCLUDED.upload_date,
                        file_path = EXCLUDED.file_path,
                        data = EXCLUDED.data;
                """, (doc_id, user_id, filename, created_at, upload_date, file_path, payload_json))

    def get_document(self, document_id):
        """
        Retrieve a document by ID. Reconstructs full dictionary from JSONB and columns.
        """
        if not document_id:
            return None
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT document_id, user_id, filename, created_at, upload_date, file_path, data
                    FROM documents WHERE document_id = %s;
                """, (document_id,))
                row = cur.fetchone()
                if not row:
                    return None
                doc = dict(row["data"]) if row.get("data") else {}
                doc["document_id"] = row["document_id"]
                doc["user_id"] = row["user_id"]
                doc["filename"] = row["filename"]
                doc["created_at"] = row["created_at"]
                doc["upload_date"] = row["upload_date"]
                doc["file_path"] = row["file_path"]
                if "s3_object_key" not in doc:
                    doc["s3_object_key"] = row["file_path"]
                return doc

    def delete_document(self, document_id):
        """
        Delete a document and its data from PostgreSQL.
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM documents WHERE document_id = %s;", (document_id,))
        return True

    def list_documents(self, force_refresh=False):
        """
        Retrieve all stored documents.
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT document_id, user_id, filename, created_at, upload_date, file_path, data
                    FROM documents ORDER BY created_at DESC;
                """)
                rows = cur.fetchall()
                results = []
                for row in rows:
                    doc = dict(row["data"]) if row.get("data") else {}
                    doc["document_id"] = row["document_id"]
                    doc["user_id"] = row["user_id"]
                    doc["filename"] = row["filename"]
                    doc["created_at"] = row["created_at"]
                    doc["upload_date"] = row["upload_date"]
                    doc["file_path"] = row["file_path"]
                    if "s3_object_key" not in doc:
                        doc["s3_object_key"] = row["file_path"]
                    results.append(doc)
                return results

    # -------------------------------------------------------------------------
    # HISTORY OPERATIONS
    # -------------------------------------------------------------------------

    def add_analysis_history(self, document_id, history_entry):
        """
        Add an analysis entry to document's analysis_history array in JSONB.
        """
        entry_json = json.dumps([history_entry])
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE documents
                    SET data = jsonb_set(
                        data,
                        '{analysis_history}',
                        COALESCE(data->'analysis_history', '[]'::jsonb) || %s::jsonb,
                        true
                    )
                    WHERE document_id = %s;
                """, (entry_json, document_id))

    def get_analysis_history(self, document_id):
        """
        Retrieve analysis history for a specific document.
        """
        doc = self.get_document(document_id)
        if not doc:
            return None
        return doc.get("analysis_history", [])

    def add_chat_message(self, document_id, chat_entry):
        """
        Append a chat message entry to document's chat_history array in JSONB.
        """
        entry_json = json.dumps([chat_entry])
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE documents
                    SET data = jsonb_set(
                        data,
                        '{chat_history}',
                        COALESCE(data->'chat_history', '[]'::jsonb) || %s::jsonb,
                        true
                    )
                    WHERE document_id = %s;
                """, (entry_json, document_id))

    def get_chat_history(self, document_id):
        """
        Retrieve chat history for a specific document.
        """
        doc = self.get_document(document_id)
        if not doc:
            return None
        return doc.get("chat_history", [])

    def add_comparison_history(self, document_id, comparison_entry):
        """
        Append a comparison record to the document's comparison_history array in JSONB.
        """
        entry_json = json.dumps([comparison_entry])
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE documents
                    SET data = jsonb_set(
                        data,
                        '{comparison_history}',
                        COALESCE(data->'comparison_history', '[]'::jsonb) || %s::jsonb,
                        true
                    )
                    WHERE document_id = %s;
                """, (entry_json, document_id))

    def get_comparison_history(self, document_id):
        """
        Retrieve comparison history for a specific document.
        """
        doc = self.get_document(document_id)
        if not doc:
            return None
        return doc.get("comparison_history", [])

    def get_comparison_history_for_user(self, user_id):
        """
        Retrieve all deduplicated comparison records for a specific user.
        """
        if not user_id:
            return []
        user_clean = str(user_id).replace("USER#", "").lower().strip()
        documents = self.list_documents()
        user_docs = [
            doc for doc in documents
            if str(doc.get("user_id", "")).replace("USER#", "").lower().strip() == user_clean
        ]

        seen_keys = set()
        all_comparisons = []

        for doc in user_docs:
            comp_list = doc.get("comparison_history", [])
            for item in comp_list:
                comp_id = item.get("comparison_id")
                if comp_id:
                    dedup_key = ("id", comp_id)
                else:
                    doc_a_id = ""
                    if isinstance(item.get("document_a"), dict):
                        doc_a_id = item.get("document_a", {}).get("document_id", "")
                    doc_b_id = ""
                    if isinstance(item.get("document_b"), dict):
                        doc_b_id = item.get("document_b", {}).get("document_id", "")
                    doc_pair = tuple(sorted([str(doc_a_id), str(doc_b_id)]))
                    ts = item.get("timestamp", "")
                    dedup_key = ("legacy", doc_pair, ts)

                if dedup_key in seen_keys:
                    continue
                seen_keys.add(dedup_key)
                all_comparisons.append(item)

        all_comparisons.sort(
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )
        return all_comparisons

    def get_comparison_by_id(self, comparison_id):
        """
        Retrieve a single comparison record by comparison_id.
        """
        if not comparison_id:
            return None
        documents = self.list_documents()
        for doc in documents:
            for item in doc.get("comparison_history", []):
                if item.get("comparison_id") == comparison_id:
                    return item
        return None

    # -------------------------------------------------------------------------
    # USER STATS
    # -------------------------------------------------------------------------

    def get_user_stats(self, user_id):
        """
        Calculate application statistics for a specific user.
        """
        if not user_id:
            return {
                "total_documents": 0,
                "total_analyses": 0,
                "total_comparisons": 0,
                "total_chats": 0
            }

        user_clean = str(user_id).replace("USER#", "").lower().strip()
        documents = self.list_documents()
        user_docs = [
            doc for doc in documents
            if str(doc.get("user_id", "")).replace("USER#", "").lower().strip() == user_clean
        ]

        total_docs = len(user_docs)
        total_analyses = 0
        total_comparisons = 0
        total_chats = 0
        seen_comp_ids = set()

        for doc in user_docs:
            total_analyses += len(doc.get("analysis_history", []))
            total_chats += len(doc.get("chat_history", []))
            for c in doc.get("comparison_history", []):
                c_id = c.get("comparison_id")
                if c_id and c_id in seen_comp_ids:
                    continue
                if c_id:
                    seen_comp_ids.add(c_id)
                total_comparisons += 1

        return {
            "total_documents": total_docs,
            "total_analyses": total_analyses,
            "total_comparisons": total_comparisons,
            "total_chats": total_chats
        }

    # -------------------------------------------------------------------------
    # ADMIN OPERATIONS
    # -------------------------------------------------------------------------

    def get_system_stats(self):
        """
        Aggregate system-wide metrics for the Admin Dashboard.
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS count FROM users;")
                user_count = cur.fetchone()["count"]

                cur.execute("SELECT COUNT(*) AS count FROM documents;")
                doc_count = cur.fetchone()["count"]

        documents = self.list_documents()
        total_analyses = 0
        total_comparisons = 0
        recent_activity = []
        seen_comp_ids = set()

        for doc in documents:
            # Analyses
            for a in doc.get("analysis_history", []):
                total_analyses += 1
                recent_activity.append({
                    "type": "analysis",
                    "title": f"Analysis on {doc.get('filename', 'Document')}",
                    "user_id": a.get("user_id", doc.get("user_id", "System")),
                    "timestamp": a.get("timestamp", doc.get("created_at", ""))
                })

            # Comparisons
            for c in doc.get("comparison_history", []):
                c_id = c.get("comparison_id")
                if c_id and c_id in seen_comp_ids:
                    continue
                if c_id:
                    seen_comp_ids.add(c_id)
                total_comparisons += 1
                doc_a = c.get("document_a", {}).get("filename", "Doc A")
                doc_b = c.get("document_b", {}).get("filename", "Doc B")
                recent_activity.append({
                    "type": "comparison",
                    "title": f"Comparison: {doc_a} vs {doc_b}",
                    "user_id": c.get("user_id", doc.get("user_id", "System")),
                    "timestamp": c.get("timestamp", doc.get("created_at", ""))
                })

        recent_activity.sort(
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )

        return {
            "total_users": user_count,
            "total_documents": doc_count,
            "total_analyses": total_analyses,
            "total_comparisons": total_comparisons,
            "recent_activity": recent_activity[:20]
        }

    def get_all_users_admin(self):
        """
        Retrieve user account list for admin overview without exposing password hashes.
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT email, full_name, role, status, created_at
                    FROM users ORDER BY created_at DESC;
                """)
                rows = cur.fetchall()
                users = []
                for row in rows:
                    email = row["email"]
                    role = "admin" if row["role"] == "admin" else "user"
                    account_status = "Active" if (row.get("status") or "active").lower() == "active" else "Inactive"
                    users.append({
                        "email": email,
                        "full_name": row.get("full_name") or email,
                        "role": role,
                        "account_status": account_status,
                        "created_at": row.get("created_at") or "N/A"
                    })
                return users

    def get_all_documents_admin(self):
        """
        Retrieve document list for admin overview.
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT document_id, filename, user_id, created_at, upload_date
                    FROM documents ORDER BY created_at DESC;
                """)
                rows = cur.fetchall()
                docs = []
                for row in rows:
                    docs.append({
                        "document_id": row["document_id"],
                        "filename": row.get("filename") or "Untitled.pdf",
                        "owner": row.get("user_id") or "Anonymous",
                        "created_at": row.get("created_at") or row.get("upload_date") or "N/A",
                        "status": "Stored"
                    })
                return docs

    def get_ai_activity_admin(self):
        """
        Retrieve AI operations activity log for admin monitoring.
        """
        documents = self.list_documents()
        activity_list = []
        for doc in documents:
            doc_name = doc.get("filename", "Document")
            user_id = doc.get("user_id", "System")

            for a in doc.get("analysis_history", []):
                act_type = str(a.get("analysis_type", a.get("history_type", "analysis"))).upper()
                activity_list.append({
                    "operation": act_type,
                    "document_name": doc_name,
                    "user_id": a.get("user_id", user_id),
                    "timestamp": a.get("timestamp", ""),
                    "status": "Completed"
                })

            for c in doc.get("chat_history", []):
                activity_list.append({
                    "operation": "Q&A (CHAT)",
                    "document_name": doc_name,
                    "user_id": c.get("user_id", user_id),
                    "timestamp": c.get("timestamp", ""),
                    "status": "Completed"
                })

        activity_list.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return activity_list

    def get_comparison_activity_admin(self):
        """
        Retrieve comparison activity log for admin monitoring.
        """
        documents = self.list_documents()
        comparisons_list = []
        seen_ids = set()

        for doc in documents:
            for c in doc.get("comparison_history", []):
                comp_id = c.get("comparison_id")
                if comp_id and comp_id in seen_ids:
                    continue
                if comp_id:
                    seen_ids.add(comp_id)

                doc_a = c.get("document_a", {}).get("filename", "Document A")
                doc_b = c.get("document_b", {}).get("filename", "Document B")
                comparisons_list.append({
                    "comparison_id": comp_id,
                    "document_a": doc_a,
                    "document_b": doc_b,
                    "user_id": c.get("user_id", doc.get("user_id", "System")),
                    "timestamp": c.get("timestamp", ""),
                    "status": "Completed"
                })

        comparisons_list.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return comparisons_list
