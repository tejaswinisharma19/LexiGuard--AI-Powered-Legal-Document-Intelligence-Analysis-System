import hashlib
import logging
import os
import uuid
from datetime import datetime, timezone

from flask import Blueprint, Response, current_app, jsonify, request, session
from werkzeug.utils import secure_filename

from ai.graph import lexiguard_graph
from document_processing.pdf_loader import extract_text_from_pdf
from document_processing.text_chunker import create_text_chunks
from extensions import (
    allowed_file,
    build_document_context,
    local_storage_service,
    login_required,
    postgresql_service,
)
from reports.analysis_report import generate_analysis_pdf
from reports.comparison_report import generate_comparison_pdf

# Service aliases for compatibility with callers and tests
dynamodb_service = postgresql_service
s3_service = local_storage_service

api_bp = Blueprint("api", __name__)


def _get_lexiguard_graph():
    import sys
    app_mod = sys.modules.get("app")
    if app_mod and hasattr(app_mod, "lexiguard_graph"):
        return app_mod.lexiguard_graph
    return lexiguard_graph


def _get_extract_text_from_pdf():
    import sys
    app_mod = sys.modules.get("app")
    if app_mod and hasattr(app_mod, "extract_text_from_pdf"):
        return app_mod.extract_text_from_pdf
    return extract_text_from_pdf


def _get_create_text_chunks():
    import sys
    app_mod = sys.modules.get("app")
    if app_mod and hasattr(app_mod, "create_text_chunks"):
        return app_mod.create_text_chunks
    return create_text_chunks


def _get_generate_analysis_pdf():
    import sys
    app_mod = sys.modules.get("app")
    if app_mod and hasattr(app_mod, "generate_analysis_pdf"):
        return app_mod.generate_analysis_pdf
    return generate_analysis_pdf


def _get_generate_comparison_pdf():
    import sys
    app_mod = sys.modules.get("app")
    if app_mod and hasattr(app_mod, "generate_comparison_pdf"):
        return app_mod.generate_comparison_pdf
    return generate_comparison_pdf



@api_bp.route("/api/upload", methods=["POST"], endpoint="upload_document")
@login_required
def upload_document():
    """
    Upload a PDF document.
    """
    if "file" not in request.files:
        return jsonify({
            "error": "No file was provided."
        }), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({
            "error": "No file was selected."
        }), 400

    if not allowed_file(file.filename):
        return jsonify({
            "error": "Only PDF files are supported."
        }), 400

    try:
        filename = secure_filename(file.filename)

        if not filename:
            return jsonify({
                "error": "Invalid filename."
            }), 400

        upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
        os.makedirs(upload_folder, exist_ok=True)

        local_file_path = os.path.join(upload_folder, filename)
        file.save(local_file_path)

        pages = _get_extract_text_from_pdf()(local_file_path)

        with open(local_file_path, "rb") as pdf_file:
            file_hash = hashlib.sha256(pdf_file.read()).hexdigest()

        storage_key = f"documents/{file_hash}_{filename}"
        storage_result = local_storage_service.upload_file(local_file_path, storage_key)

        file_size = os.path.getsize(local_file_path)
        page_count = len(pages)
        document_id = str(uuid.uuid4())

        document_metadata = {
            "document_id": document_id,
            "user_id": session.get("user_id", ""),
            "filename": filename,
            "file_size_bytes": file_size,
            "page_count": page_count,
            "upload_timestamp": datetime.now(timezone.utc).isoformat(),
            "file_path": storage_result.get("file_path", storage_key),
            "s3_object_key": storage_result.get("object_key", storage_key),
            "content_hash": file_hash,
            "processing_status": "processed"
        }

        postgresql_service.save_document(document_metadata)

        return jsonify({
            "message": "PDF uploaded successfully.",
            "document": document_metadata
        }), 201

    except Exception as error:
        logging.exception("Error in upload_document: %s", error)
        return jsonify({
            "error": "Unable to upload the document."
        }), 500


@api_bp.route("/api/documents", methods=["GET"], endpoint="list_documents")
@login_required
def list_documents():
    """
    Retrieve all uploaded document metadata from DynamoDB.
    """
    try:
        documents = postgresql_service.list_documents()
        formatted_documents = []

        for document in documents:
            doc_id = str(document.get("document_id", ""))

            if doc_id.startswith("USER#"):
                continue

            if not document.get("s3_object_key") and not document.get("filename"):
                continue

            doc_owner = document.get("user_id")
            current_user = session.get("user_id")
            if doc_owner and current_user and doc_owner != current_user:
                continue

            formatted_documents.append({
                "document_id": document["document_id"],
                "filename": document.get("filename", "unknown.pdf"),
                "file_size_bytes": int(document.get("file_size_bytes") or 0),
                "page_count": int(document.get("page_count") or 0),
                "upload_timestamp": document.get("upload_timestamp", ""),
                "s3_object_key": document.get("s3_object_key", ""),
                "content_hash": document.get("content_hash"),
                "processing_status": document.get("processing_status", "processed")
            })

        return jsonify({
            "documents": formatted_documents,
            "total_documents": len(formatted_documents)
        })

    except Exception as error:
        logging.exception("Error in list_documents: %s", error)
        return jsonify({
            "error": "Unable to retrieve documents."
        }), 500


@api_bp.route("/api/documents/<document_id>", methods=["GET"], endpoint="get_document")
@login_required
def get_document(document_id):
    """
    Retrieve metadata for a specific document.
    """
    if not document_id:
        return jsonify({
            "error": "Document ID is required."
        }), 400

    try:
        document = postgresql_service.get_document(document_id)

        if not document:
            return jsonify({
                "error": "Document not found."
            }), 404

        formatted_document = {
            "document_id": document["document_id"],
            "filename": document.get("filename", "unknown.pdf"),
            "file_size_bytes": int(document.get("file_size_bytes") or 0),
            "page_count": int(document.get("page_count") or 0),
            "upload_timestamp": document.get("upload_timestamp", ""),
            "s3_object_key": document.get("s3_object_key", ""),
            "content_hash": document.get("content_hash"),
            "processing_status": document.get("processing_status", "processed")
        }

        return jsonify({
            "document": formatted_document
        })

    except Exception as error:
        logging.exception("Error in get_document: %s", error)
        return jsonify({
            "error": "Unable to retrieve the document."
        }), 500


@api_bp.route("/api/documents/<document_id>/history", methods=["GET"], endpoint="get_analysis_history")
@login_required
def get_analysis_history(document_id):
    """
    Retrieve analysis history for a document (Summary, Risk, Clause Extraction only).
    """
    if not document_id:
        return jsonify({
            "error": "Document ID is required."
        }), 400

    try:
        document = postgresql_service.get_document(document_id)

        if not document:
            return jsonify({
                "error": "Document not found."
            }), 404

        doc_owner = document.get("user_id")
        current_user = session.get("user_id")
        if doc_owner and current_user and doc_owner != current_user:
            return jsonify({
                "error": "Unauthorized access to document history."
            }), 403

        raw_history = postgresql_service.get_analysis_history(document_id) or []

        filtered_history = [
            entry for entry in raw_history
            if entry.get("analysis_type") in ["summary", "risk", "clause"]
            or (entry.get("history_type") == "analysis" and entry.get("analysis_type") != "qa")
        ]

        return jsonify({
            "document_id": document_id,
            "filename": document["filename"],
            "history": filtered_history,
            "total_analyses": len(filtered_history)
        })

    except Exception as error:
        logging.exception("Error in get_analysis_history: %s", error)
        return jsonify({
            "error": "Unable to retrieve analysis history."
        }), 500


@api_bp.route("/api/documents/<document_id>/chat-history", methods=["GET"], endpoint="get_chat_history")
@login_required
def get_chat_history(document_id):
    """
    Retrieve chat history for a document (Q&A interactions only).
    """
    if not document_id:
        return jsonify({
            "error": "Document ID is required."
        }), 400

    try:
        document = postgresql_service.get_document(document_id)

        if not document:
            return jsonify({
                "error": "Document not found."
            }), 404

        doc_owner = document.get("user_id")
        current_user = session.get("user_id")
        if doc_owner and current_user and doc_owner != current_user:
            return jsonify({
                "error": "Unauthorized access to document history."
            }), 403

        raw_history = postgresql_service.get_chat_history(document_id) or []

        filtered_history = [
            entry for entry in raw_history
            if entry.get("user_message") or entry.get("history_type") == "chat"
        ]

        return jsonify({
            "document_id": document_id,
            "filename": document["filename"],
            "chat_history": filtered_history,
            "total_messages": len(filtered_history)
        })

    except Exception as error:
        logging.exception("Error in get_chat_history: %s", error)
        return jsonify({
            "error": "Unable to retrieve chat history."
        }), 500


@api_bp.route("/api/comparison-history", methods=["GET"], endpoint="get_user_comparison_history")
@login_required
def get_user_comparison_history():
    """
    Retrieve all comparison history records for the logged-in user.
    """
    try:
        current_user = session.get("user_id")
        history = postgresql_service.get_comparison_history_for_user(current_user)
        return jsonify({
            "comparison_history": history,
            "total_comparisons": len(history)
        })
    except Exception as error:
        logging.exception("Error in get_user_comparison_history: %s", error)
        return jsonify({
            "error": "Unable to retrieve comparison history."
        }), 500


@api_bp.route("/api/user/stats", methods=["GET"], endpoint="user_stats_api")
@login_required
def user_stats_api():
    """
    Retrieve statistics for the currently logged-in user.
    """
    try:
        current_user = session.get("user_id")
        stats = postgresql_service.get_user_stats(current_user)
        return jsonify(stats), 200
    except Exception as error:
        logging.exception("Error in user_stats_api: %s", error)
        return jsonify({
            "error": "Unable to retrieve user statistics."
        }), 500


@api_bp.route("/api/documents/<document_id>/comparison-history", methods=["GET"], endpoint="get_document_comparison_history")
@login_required
def get_document_comparison_history(document_id):
    """
    Retrieve comparison history for a specific document.
    """
    if not document_id:
        return jsonify({
            "error": "Document ID is required."
        }), 400

    try:
        document = postgresql_service.get_document(document_id)
        if not document:
            return jsonify({
                "error": "Document not found."
            }), 404

        doc_owner = document.get("user_id")
        current_user = session.get("user_id")
        if doc_owner and current_user and doc_owner != current_user:
            return jsonify({
                "error": "Unauthorized access to document history."
            }), 403

        history = postgresql_service.get_comparison_history(document_id) or []
        return jsonify({
            "document_id": document_id,
            "filename": document.get("filename", "unknown.pdf"),
            "comparison_history": history,
            "total_comparisons": len(history)
        })
    except Exception as error:
        logging.exception("Error in get_document_comparison_history: %s", error)
        return jsonify({
            "error": "Unable to retrieve document comparison history."
        }), 500


@api_bp.route("/api/documents/<document_id>", methods=["DELETE"], endpoint="delete_document")
@login_required
def delete_document(document_id):
    """
    Delete a document from S3 and DynamoDB.
    """
    if not document_id:
        return jsonify({
            "error": "Document ID is required."
        }), 400

    try:
        document = postgresql_service.get_document(document_id)

        if not document:
            return jsonify({
                "error": "Document not found."
            }), 404

        object_key = document.get("file_path") or document.get("s3_object_key")

        if object_key:
            local_storage_service.delete_file(object_key)

        postgresql_service.delete_document(document_id)

        return jsonify({
            "message": "Document deleted successfully.",
            "document_id": document_id
        }), 200

    except Exception as error:
        logging.exception("Error in delete_document: %s", error)
        return jsonify({
            "error": "Unable to delete document."
        }), 500


@api_bp.route("/api/constitution", methods=["POST"], endpoint="query_constitution")
@login_required
def query_constitution():
    """
    Query the Constitution of India knowledge base using Constitutional RAG.
    Does NOT require document_id or uploaded document lookup.
    """
    data = request.get_json() or {}
    question = data.get("question", "").strip()

    if not question:
        return jsonify({
            "error": "Question is required."
        }), 400

    try:
        initial_state = {
            "user_query": question,
            "intent": "constitution",
            "chunks": [],
            "document_id": "",
            "content_hash": "",
            "document_a_context": "",
            "document_b_context": "",
            "document_a_chunks": [],
            "document_b_chunks": [],
            "response": "",
            "sources": []
        }

        result = _get_lexiguard_graph().invoke(initial_state)

        return jsonify({
            "intent": result.get("intent", "constitution"),
            "response": result.get("response", ""),
            "sources": result.get("sources", [])
        }), 200

    except Exception as error:
        logging.exception("Error in query_constitution: %s", error)
        return jsonify({
            "error": "Unable to access the Constitution knowledge base. Please try again."
        }), 500


@api_bp.route("/api/analyze", methods=["POST"], endpoint="analyze_document")
@login_required
def analyze_document():
    """
    Analyze a document using the LangGraph + RAG pipeline.
    """
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body must contain JSON."
        }), 400

    document_id = data.get("document_id")
    question = data.get("question")

    if document_id in ["constitution_query", "constitution"]:
        return query_constitution()

    if not document_id:
        return jsonify({
            "error": "Document ID is required."
        }), 400

    if not question:
        return jsonify({
            "error": "Question is required."
        }), 400

    question = question.strip()

    if not question:
        return jsonify({
            "error": "Question cannot be empty."
        }), 400

    temporary_file_path = None
    upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")

    try:
        document = postgresql_service.get_document(document_id)

        if not document:
            return jsonify({
                "error": "Document not found."
            }), 404

        storage_key = document.get("file_path") or document.get("s3_object_key")

        if not storage_key or not s3_service.file_exists(storage_key):
            return jsonify({
                "error": "Document file not found in storage."
            }), 404

        os.makedirs(upload_folder, exist_ok=True)
        temporary_file_path = os.path.join(upload_folder, f"{document_id}.pdf")

        s3_service.download_file(storage_key, temporary_file_path)
        pages = _get_extract_text_from_pdf()(temporary_file_path)
        chunks = _get_create_text_chunks()(pages)

        initial_state = {
            "user_query": question,
            "intent": "",
            "chunks": chunks,
            "document_id": document_id,
            "content_hash": document.get("content_hash", ""),
            "document_a_context": "",
            "document_b_context": "",
            "document_a_chunks": [],
            "document_b_chunks": [],
            "response": "",
            "sources": []
        }

        result = _get_lexiguard_graph().invoke(initial_state)

        if result["intent"] == "qa":
            chat_history_entry = {
                "message_id": str(uuid.uuid4()),
                "history_type": "chat",
                "user_message": question,
                "assistant_response": result["response"],
                "sources": [
                    {
                        "page_number": source["page_number"],
                        "chunk_number": source["chunk_number"]
                    }
                    for source in result.get("sources", [])
                ],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            postgresql_service.add_chat_message(document_id, chat_history_entry)
        else:
            analysis_history_entry = {
                "analysis_id": str(uuid.uuid4()),
                "history_type": "analysis",
                "analysis_type": result["intent"],
                "question": question,
                "response": result["response"],
                "sources": [
                    {
                        "page_number": source["page_number"],
                        "chunk_number": source["chunk_number"]
                    }
                    for source in result.get("sources", [])
                ],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            postgresql_service.add_analysis_history(document_id, analysis_history_entry)

        return jsonify({
            "document_id": document_id,
            "filename": document.get("filename", "unknown.pdf"),
            "question": question,
            "intent": result["intent"],
            "response": result["response"],
            "sources": [
                {
                    "page_number": source["page_number"],
                    "chunk_number": source["chunk_number"]
                }
                for source in result["sources"]
            ]
        })

    except RuntimeError as error:
        return jsonify({
            "error": str(error)
        }), 503

    except Exception as error:
        logging.exception("Error in analyze_document: %s", error)
        return jsonify({
            "error": "Unable to analyze the document."
        }), 500

    finally:
        if temporary_file_path and os.path.exists(temporary_file_path):
            try:
                os.remove(temporary_file_path)
            except OSError:
                pass


@api_bp.route("/api/compare", methods=["POST"], endpoint="compare_documents")
@login_required
def compare_documents():
    """
    Compare two legal documents using the LangGraph comparison workflow.
    """
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body must contain JSON."
        }), 400

    document_a_id = data.get("document_a_id")
    document_b_id = data.get("document_b_id")

    if not document_a_id:
        return jsonify({
            "error": "Document A ID is required."
        }), 400

    if not document_b_id:
        return jsonify({
            "error": "Document B ID is required."
        }), 400

    if document_a_id == document_b_id:
        return jsonify({
            "error": "Document A and Document B must be different."
        }), 400

    document_a_path = None
    document_b_path = None
    upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")

    try:
        document_a = postgresql_service.get_document(document_a_id)

        if not document_a:
            return jsonify({
                "error": "Document A not found."
            }), 404

        document_b = postgresql_service.get_document(document_b_id)

        if not document_b:
            return jsonify({
                "error": "Document B not found."
            }), 404

        key_a = document_a.get("file_path") or document_a.get("s3_object_key")
        key_b = document_b.get("file_path") or document_b.get("s3_object_key")

        if not key_a or not s3_service.file_exists(key_a):
            return jsonify({
                "error": "Document A file not found in storage."
            }), 404

        if not key_b or not s3_service.file_exists(key_b):
            return jsonify({
                "error": "Document B file not found in storage."
            }), 404

        os.makedirs(upload_folder, exist_ok=True)

        document_a_path = os.path.join(upload_folder, f"{document_a_id}.pdf")
        document_b_path = os.path.join(upload_folder, f"{document_b_id}.pdf")

        s3_service.download_file(key_a, document_a_path)
        s3_service.download_file(key_b, document_b_path)

        document_a_pages = _get_extract_text_from_pdf()(document_a_path)
        document_b_pages = _get_extract_text_from_pdf()(document_b_path)

        document_a_chunks = _get_create_text_chunks()(document_a_pages)
        document_b_chunks = _get_create_text_chunks()(document_b_pages)

        document_a_context = build_document_context(document_a_chunks, "DOCUMENT A")
        document_b_context = build_document_context(document_b_chunks, "DOCUMENT B")

        initial_state = {
            "user_query": "Compare Document A and Document B.",
            "intent": "",
            "chunks": [],
            "document_a_context": document_a_context,
            "document_b_context": document_b_context,
            "document_a_chunks": document_a_chunks,
            "document_b_chunks": document_b_chunks,
            "response": "",
            "sources": []
        }

        result = _get_lexiguard_graph().invoke(initial_state)

        comparison_entry = {
            "comparison_id": str(uuid.uuid4()),
            "user_id": session.get("user_id", ""),
            "history_type": "comparison",
            "document_a": {
                "document_id": document_a_id,
                "filename": document_a.get("filename", "unknown.pdf")
            },
            "document_b": {
                "document_id": document_b_id,
                "filename": document_b.get("filename", "unknown.pdf")
            },
            "response": result["response"],
            "sources": result.get("sources", []),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        postgresql_service.add_comparison_history(document_a_id, comparison_entry)
        postgresql_service.add_comparison_history(document_b_id, comparison_entry)

        return jsonify({
            "document_a": {
                "document_id": document_a_id,
                "filename": document_a["filename"]
            },
            "document_b": {
                "document_id": document_b_id,
                "filename": document_b["filename"]
            },
            "intent": result["intent"],
            "response": result["response"],
            "sources": result["sources"]
        })

    except RuntimeError as error:
        return jsonify({
            "error": str(error)
        }), 503

    except Exception as error:
        logging.exception("Error in compare_documents: %s", error)
        return jsonify({
            "error": "Unable to compare the documents."
        }), 500

    finally:
        for temporary_path in [document_a_path, document_b_path]:
            if temporary_path and os.path.exists(temporary_path):
                try:
                    os.remove(temporary_path)
                except OSError:
                    pass


@api_bp.route("/api/reports/analysis/<document_id>", methods=["GET"], endpoint="download_analysis_report")
@login_required
def download_analysis_report(document_id):
    """
    Generate and download PDF analysis report for a document using saved history.
    Does NOT rerun LLM, LangGraph, or RAG inference.
    """
    try:
        user_id = session.get("user_id", "")
        document = postgresql_service.get_document(document_id)
        if not document:
            return jsonify({
                "error": "Document not found."
            }), 404

        doc_user = str(document.get("user_id", "")).replace("USER#", "").lower().strip()
        user_clean = str(user_id).replace("USER#", "").lower().strip()

        user_rec = postgresql_service.get_user_by_email(user_clean)
        is_admin = bool(user_rec and user_rec.get("role") == "admin")

        if doc_user and doc_user != user_clean and not is_admin:
            return jsonify({
                "error": "Forbidden: You do not have access to this document report."
            }), 403

        history = postgresql_service.get_analysis_history(document_id) or []
        analysis_id = request.args.get("analysis_id")

        target_analysis = None
        if analysis_id:
            for item in history:
                if item.get("analysis_id") == analysis_id:
                    target_analysis = item
                    break
        else:
            if history:
                target_analysis = history[-1]

        if not target_analysis:
            return jsonify({
                "error": "No analysis history found for this document."
            }), 404

        filename = document.get("filename", "document.pdf")
        pdf_buffer = _get_generate_analysis_pdf()(filename, target_analysis)
        clean_name = secure_filename(filename) or "analysis.pdf"

        return Response(
            pdf_buffer.read(),
            mimetype="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="LexiGuard_Analysis_{clean_name}.pdf"'
            }
        )
    except Exception as error:
        logging.exception("Error in download_analysis_report: %s", error)
        return jsonify({
            "error": "Unable to generate analysis report."
        }), 500


@api_bp.route("/api/reports/comparison/<comparison_id>", methods=["GET"], endpoint="download_comparison_report")
@login_required
def download_comparison_report(comparison_id):
    """
    Generate and download PDF comparison report using saved comparison history.
    Does NOT rerun LLM, LangGraph, or RAG inference.
    """
    try:
        user_id = session.get("user_id", "")
        comparison_entry = postgresql_service.get_comparison_by_id(comparison_id)
        if not comparison_entry:
            return jsonify({
                "error": "Comparison record not found."
            }), 404

        comp_user = str(comparison_entry.get("user_id", "")).replace("USER#", "").lower().strip()
        user_clean = str(user_id).replace("USER#", "").lower().strip()

        user_rec = postgresql_service.get_user_by_email(user_clean)
        is_admin = bool(user_rec and user_rec.get("role") == "admin")

        if comp_user and comp_user != user_clean and not is_admin:
            return jsonify({
                "error": "Forbidden: You do not have access to this comparison report."
            }), 403

        pdf_buffer = _get_generate_comparison_pdf()(comparison_entry)
        short_id = comparison_id[:8]

        return Response(
            pdf_buffer.read(),
            mimetype="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="LexiGuard_Comparison_{short_id}.pdf"'
            }
        )
    except Exception as error:
        logging.exception("Error in download_comparison_report: %s", error)
        return jsonify({
            "error": "Unable to generate comparison report."
        }), 500
