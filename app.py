import logging
from flask import Flask, request

from config import Config
from ai.graph import lexiguard_graph
from document_processing.pdf_loader import extract_text_from_pdf
from document_processing.text_chunker import create_text_chunks
from reports.analysis_report import generate_analysis_pdf
from reports.comparison_report import generate_comparison_pdf
import extensions
from routes.admin import admin_bp
from routes.analysis import analysis_bp
from routes.api import api_bp
from routes.auth import auth_bp
from routes.documents import documents_bp

app = Flask(__name__)
app.config.from_object(Config)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["ASSET_VERSION"] = "2.5.0"
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

@app.after_request
def add_cache_control_header(response):
    if request.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


# Re-export service singletons, decorators, utilities, and AI modules for full test compatibility
postgresql_service = extensions.postgresql_service
local_storage_service = extensions.local_storage_service
s3_service = extensions.s3_service
ses_service = extensions.ses_service
sns_service = extensions.sns_service
gmail_service = extensions.gmail_service
dynamodb_service = extensions.dynamodb_service

login_required = extensions.login_required
admin_required = extensions.admin_required
allowed_file = extensions.allowed_file
build_document_context = extensions.build_document_context
lexiguard_graph = lexiguard_graph
extract_text_from_pdf = extract_text_from_pdf
create_text_chunks = create_text_chunks
generate_analysis_pdf = generate_analysis_pdf
generate_comparison_pdf = generate_comparison_pdf

# Register Flask Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(documents_bp)
app.register_blueprint(analysis_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(api_bp)

# Alias blueprint endpoints to top-level endpoint names for full url_for compatibility
for rule in list(app.url_map.iter_rules()):
    if "." in rule.endpoint and rule.endpoint != "static":
        short_endpoint = rule.endpoint.split(".", 1)[1]
        view_func = app.view_functions.get(rule.endpoint)
        if view_func and short_endpoint not in [r.endpoint for r in app.url_map.iter_rules()]:
            app.add_url_rule(
                rule.rule,
                endpoint=short_endpoint,
                view_func=view_func,
                methods=list(rule.methods) if rule.methods else None
            )


if __name__ == "__main__":
    app.run(debug=True)