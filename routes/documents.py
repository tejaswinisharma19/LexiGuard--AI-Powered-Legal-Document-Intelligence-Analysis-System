import logging
import os

from flask import Blueprint, Response, current_app, render_template, session

from extensions import local_storage_service, login_required, postgresql_service

documents_bp = Blueprint("documents", __name__)


@documents_bp.route("/documents", endpoint="documents_page")
@login_required
def documents_page():
    """
    Render the document management page.
    """
    return render_template(
        "documents.html",
        user_name=session.get("user_name", "User"),
        user_id=session.get("user_id", "")
    )


@documents_bp.route("/documents/<document_id>/view", methods=["GET"], endpoint="view_pdf_document")
@login_required
def view_pdf_document(document_id):
    """
    Stream a protected PDF file directly from local storage for browser viewing.
    Requires authentication and verifies document ownership.
    """
    if not document_id or str(document_id).startswith("USER#"):
        return "Document not found.", 404

    try:
        document = postgresql_service.get_document(document_id)
        if not document:
            return "Document not found.", 404

        doc_owner = document.get("user_id")
        current_user = session.get("user_id")
        if doc_owner and current_user and doc_owner != current_user:
            return "Unauthorized access to document.", 403

        storage_key = document.get("file_path") or document.get("s3_object_key")
        if not storage_key or not local_storage_service.file_exists(storage_key):
            return "Document file not found in storage.", 404

        upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
        os.makedirs(upload_folder, exist_ok=True)
        temp_pdf_path = os.path.join(
            upload_folder, f"view_{document_id}.pdf"
        )
        local_storage_service.download_file(storage_key, temp_pdf_path)

        with open(temp_pdf_path, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()

        if os.path.exists(temp_pdf_path):
            try:
                os.remove(temp_pdf_path)
            except OSError:
                pass

        filename = document.get("filename", "document.pdf")
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={
                "Content-Type": "application/pdf",
                "Content-Disposition": f'inline; filename="{filename}"'
            }
        )

    except Exception as error:
        logging.exception("Error in view_document: %s", error)
        return "Unable to retrieve document view.", 500
