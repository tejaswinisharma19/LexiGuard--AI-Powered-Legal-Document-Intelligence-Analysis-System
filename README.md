# LexiGuard

## AI-Powered Legal Document Intelligence & Analysis System

LexiGuard is an AI-assisted legal document analysis system that helps users understand and analyze PDF-based legal documents through document question answering, summarization, clause extraction, risk identification, and document comparison.

The project combines Python, Flask, RAG, LangChain, LangGraph, Gemini, scikit-learn, PyMuPDF, and AWS S3.

> **Disclaimer:** LexiGuard provides AI-assisted document analysis for informational purposes only. It is not a substitute for professional legal advice.

---

## Features

- PDF document upload
- Secure document storage using private Amazon S3
- PDF text extraction
- Text chunking with metadata
- Local TF-IDF based retrieval
- Retrieval-Augmented Generation (RAG)
- Document question answering
- Document summarization
- Legal clause extraction
- Potential risk identification
- Document comparison
- LangGraph-based request routing
- Source/page references
- Flask REST APIs

---

## Architecture

```text
User
  |
  v
Flask API
  |
  +----------------------+
  |                      |
  v                      v
PDF Validation       Private S3
  |                      |
  v                      |
PDF Processing <---------+
  |
  v
Text Extraction
  |
  v
Text Chunking
  |
  v
TF-IDF Retrieval
  |
  v
LangGraph
  |
  +----------+-----------+----------+
  |          |           |          |
  v          v           v          v
  QA      Summary     Clauses     Risks
  |
  v
RAG
  |
  v
Gemini