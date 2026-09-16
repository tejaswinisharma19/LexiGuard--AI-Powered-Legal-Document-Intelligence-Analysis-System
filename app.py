import os

from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename

from config import Config
from aws.s3_service import S3Service
from document_processing.pdf_loader import extract_text_from_pdf
from document_processing.text_chunker import create_text_chunks
from ai.graph import lexiguard_graph


app = Flask(__name__)
app.config.from_object(Config)


# -----------------------------
# Application Configuration
# -----------------------------

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

s3_service = S3Service()


# -----------------------------
# Helper Functions
# -----------------------------

def allowed_file(filename):
    """
    Check whether the uploaded file has an allowed extension.
    """
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# -----------------------------
# Home Route
# -----------------------------

@app.route("/")
def home():
    """
    Check whether the LexiGuard application is running.
    """
    return "LexiGuard is running successfully!"


# -----------------------------
# Document Upload API
# -----------------------------

@app.route("/api/upload", methods=["POST"])
def upload_document():
    """
    Upload a PDF, process it, and store it in S3.
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
        # Secure the uploaded filename
        filename = secure_filename(file.filename)

        if not filename:
            return jsonify({
                "error": "Invalid filename."
            }), 400

        # Create temporary local storage
        os.makedirs(
            app.config["UPLOAD_FOLDER"],
            exist_ok=True
        )

        local_file_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        # Save uploaded PDF temporarily
        file.save(local_file_path)

        # Verify that the PDF contains extractable text
        pages = extract_text_from_pdf(
            local_file_path
        )

        # Define S3 object location
        s3_object_key = f"documents/{filename}"

        # Upload PDF to S3
        s3_result = s3_service.upload_file(
            local_file_path,
            s3_object_key
        )

        # Collect metadata
        file_size = os.path.getsize(
            local_file_path
        )

        page_count = len(pages)

        return jsonify({
            "message": "PDF uploaded successfully.",
            "document": {
                "filename": filename,
                "file_size_bytes": file_size,
                "page_count": page_count,
                "processing_status": "uploaded",
                "storage": "s3",
                "s3_object_key": s3_result["object_key"]
            }
        }), 201

    except Exception as error:
        return jsonify({
            "error": "Unable to upload the document.",
            "details": str(error)
        }), 500


# -----------------------------
# Document Analysis API
# -----------------------------

@app.route("/api/analyze", methods=["POST"])
def analyze_document():
    """
    Analyze a PDF stored in S3 using the LexiGuard AI pipeline.
    """

    # Read JSON request
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body must contain JSON."
        }), 400

    filename = data.get("filename")
    question = data.get("question")

    # Validate filename
    if not filename:
        return jsonify({
            "error": "Filename is required."
        }), 400

    # Validate question
    if not question:
        return jsonify({
            "error": "Question is required."
        }), 400

    # Secure filename
    safe_filename = secure_filename(filename)

    if safe_filename != filename:
        return jsonify({
            "error": "Invalid filename."
        }), 400

    # Validate extension
    if not allowed_file(safe_filename):
        return jsonify({
            "error": "Only PDF files are supported."
        }), 400

    # S3 location of the document
    s3_object_key = f"documents/{safe_filename}"

    try:
        # Check whether the document exists in S3
        if not s3_service.file_exists(s3_object_key):
            return jsonify({
                "error": "Document not found in S3."
            }), 404

        # Create temporary local directory
        os.makedirs(
            app.config["UPLOAD_FOLDER"],
            exist_ok=True
        )

        # Temporary local path
        temporary_file_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            safe_filename
        )

        # Download PDF from S3
        s3_service.download_file(
            s3_object_key,
            temporary_file_path
        )

        # Extract text from PDF
        pages = extract_text_from_pdf(
            temporary_file_path
        )

        # Create text chunks
        chunks = create_text_chunks(
            pages
        )

        # Initial LangGraph state
        initial_state = {
            "user_query": question,
            "intent": "",
            "chunks": chunks,
            "response": "",
            "sources": []
        }

        # Execute LangGraph workflow
        result = lexiguard_graph.invoke(
            initial_state
        )

        # Return analysis result
        return jsonify({
            "filename": safe_filename,
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

    except Exception as error:
        return jsonify({
            "error": "Unable to analyze the document.",
            "details": str(error)
        }), 500


# -----------------------------
# Application Entry Point
# -----------------------------

if __name__ == "__main__":
    app.run(debug=True)