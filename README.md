# LexiGuard — AI-Powered Legal Document Intelligence & Analysis System

LexiGuard is a local-first, zero-cost AI legal document intelligence platform that provides grounded document Q&A, structured summarization, clause extraction, risk analysis, and side-by-side contract comparison with exact page and chunk citations.

> [!IMPORTANT]
> **Legal Analysis Disclaimer:** LexiGuard provides AI-assisted document analysis for informational purposes only. It is not a substitute for professional legal advice.

---

## 🌟 Overview & Problem Statement

Legal documents (contracts, terms of service, NDAs, software agreements) are dense, lengthy, and filled with technical jargon. Manually identifying potential risks, key obligations, or differences across contract versions takes substantial time. 

**LexiGuard** automates legal document intelligence through a local-first, RAG-first hybrid architecture:
- **Local-First Processing:** Text extraction (PyMuPDF), TF-IDF vector retrieval (scikit-learn), and deterministic intent routing (LangGraph) run locally in Python with zero external API calls.
- **RAG-First QA Pipeline:** TF-IDF similarity scoring runs BEFORE any LLM invocation. Queries with insufficient document evidence automatically return *"Not found in the document."* without calling the LLM (0 LLM calls).
- **Answer Caching:** Lightweight in-memory answer caching prevents repeated LLM invocations for identical questions on the same document version.
- **Gemini 3.5 Flash-Lite & Mock Mode:** Uses **Gemini 3.5 Flash-Lite** (`LLM_PROVIDER=gemini`) for live inference and a deterministic **Mock LLM mode** (`LLM_PROVIDER=mock`) for zero-quota local development and testing.
- **Strict History Categorization:** Separates Q&A into **Chat History**, Document Summary / Risk / Clause into **Analysis History**, and contract comparisons into **Comparison History**.
- **PostgreSQL & Local Storage:** Metadata, users, analysis history, and chat history persist in **PostgreSQL** (`lexiguard_db`) with JSONB support; PDF files are stored in the local `uploads/` directory with path traversal protection.

---

## 🏗️ Architecture

```text
                                  +-----------------------+
                                  |   User (Web / API)    |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  |   Flask Server App    |
                                  +-----+-----------+-----+
                                        |           |
                        +--------------+           +--------------+
                        v                                         v
              +-------------------+                     +-------------------+
              |   Local Storage   |                     | PostgreSQL DB     |
              |     (uploads/)    |                     | (users, documents)|
              +-------------------+                     +-------------------+
                        |
                        v
              +-------------------+
              | PDF Text Extraction| (PyMuPDF + Normalization)
              +---------+---------+
                        |
                        v
              +-------------------+
              |   Text Chunker    | (RecursiveCharacterTextSplitter)
              +---------+---------+
                        |
                        v
              +-------------------+
              |  Answer Cache     | (Hash-based Q&A Cache)
              +---------+---------+
                        |
                        v
              +-------------------+
              |  TF-IDF Retriever | (Zero-Cost Local Retrieval & Score Check)
              +---------+---------+
                        |
                        v
              +-------------------+
              | LangGraph Router  | (Deterministic Python Intent Routing)
              +----+----+----+----+
                   |    |    |    \
        +----------+    |    |     +--------------------+
        v               v    v                          v
    [QA Node]     [Summary] [Clause] [Risk]      [Comparison Node]
        |               |    |    |                     |
        +---------------+----+----+                     |
                        |                               |
                        v                               v
              +-------------------+           +-------------------+
              | Grounded RAG      |           | Structured JSON   |
              | Gemini 3.5 LLM    |           | Comparison Engine |
              | (or Mock Mode)    |           |                   |
              +-------------------+           +-------------------+
```

---

## 🛠️ Technology Stack

- **Backend Framework:** Python 3.14, Flask 3.1.3
- **AI & RAG:** LangChain Text Splitters, LangGraph 1.2.11, Google GenAI SDK 2.23.0 (**Gemini 3.5 Flash-Lite**)
- **Vector Retrieval:** scikit-learn 1.9.1 (TF-IDF Vectorizer & Cosine Similarity)
- **PDF Processing:** PyMuPDF 1.28.2 (fitz)
- **Cloud Infrastructure:** AWS Boto3 1.43.95 (Amazon S3, AWS DynamoDB)
- **Frontend:** HTML5, Glassmorphic CSS3, JavaScript (ES6+ async/await)

---

## 📂 Project Structure

```text
lexiguard/
│
├── app.py                      # Main Flask web application & REST API routes
├── config.py                   # Centralized configuration & environment loader
├── requirements.txt            # Python dependencies
├── .env                        # Local environment variables (git-ignored)
├── README.md                   # Project documentation
│
├── ai/                         # AI & RAG Engine
│   ├── __init__.py
│   ├── embeddings.py           # TF-IDF local text representation
│   ├── retriever.py            # Cosine similarity retriever with thresholds
│   ├── prompts.py              # Grounded legal prompts & JSON comparison schemas
│   ├── llm.py                  # Gemini 3.5 Flash-Lite LLM & Mock mode interface
│   ├── cache.py                # Deterministic answer cache for Q&A queries
│   ├── rag.py                  # Grounded RAG Q&A engine with negative retrieval filtering
│   └── graph.py                # LangGraph state machine & deterministic intent routing
│
├── aws/                        # Cloud Services Infrastructure
│   ├── __init__.py
│   ├── s3_service.py           # Amazon S3 upload, download, delete operations
│   └── dynamodb_service.py     # DynamoDB metadata and history operations
│
├── document_processing/        # PDF Ingestion & Chunking
│   ├── __init__.py
│   ├── pdf_loader.py           # PyMuPDF text extraction & symbol normalization
│   └── text_chunker.py         # Recursive character chunking with page metadata
│
├── static/                     # Web Assets (CSS, JS)
│   ├── css/                    # Dark glassmorphism stylesheet
│   └── js/                     # Dashboard & document interaction scripts
│
├── templates/                  # HTML Views
│   ├── dashboard.html          # Main overview dashboard
│   ├── documents.html          # Document management & Ask LexiGuard AI workspace
│   ├── compare.html            # Side-by-side document comparison
│   ├── history.html            # Analysis History (Summary, Risk, Clause)
│   ├── chat_history.html       # Chat History (Conversational Q&A)
│   └── comparison_history.html # Comparison History
│
└── tests/                      # Automated Test Suites
    ├── test_analysis_history_summarizer.py
    ├── test_history_architecture.py
    ├── test_llm_provider_mode.py
    ├── test_rag_cache_negative.py
    ├── test_dashboard_qa.py
    └── test_compare_endpoint.py
```

---

## ⚙️ Environment Configuration (`.env`)

Create a `.env` file in the root directory:

```ini
SECRET_KEY=lexiguard-development-key
GEMINI_API_KEY=your_gemini_api_key_here
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-3.5-flash-lite

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=lexiguard_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```

> [!TIP]
> **Mock LLM Mode for Testing:** To run development and testing with zero external API calls and zero quota consumption, set `LLM_PROVIDER=mock` in your `.env` file.

---

## 🔌 API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/dashboard` | Main dashboard view |
| `GET` | `/documents` | Document management & AI workspace |
| `GET` | `/compare` | Document comparison interface |
| `GET` | `/history` | Analysis History view (Summary, Risk, Clause) |
| `GET` | `/chat-history` | Chat History view (Q&A interactions) |
| `GET` | `/comparison-history` | Comparison History view |
| `POST` | `/api/upload` | Upload PDF, extract text, store in local uploads/, save PostgreSQL metadata |
| `GET` | `/api/documents` | List user documents stored in PostgreSQL |
| `DELETE`| `/api/documents/<id>` | Delete document from local storage and PostgreSQL |
| `GET` | `/api/documents/<id>/history` | Retrieve document analysis history |
| `GET` | `/api/documents/<id>/chat-history` | Retrieve document chat Q&A history |
| `POST` | `/api/analyze` | Execute Q&A, Summary, Risk, or Clause analysis via RAG + LangGraph |
| `POST` | `/api/compare` | Compare two documents side-by-side using 7 legal categories |

---

## 🧪 Testing

Run tests safely without consuming API quota:

```powershell
$env:PYTHONPATH="."
$env:LLM_PROVIDER="mock"
python -m unittest discover -s tests
```