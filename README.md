# ScholarMind

ScholarMind is an AI-powered academic research assistant built with **React** and **Django**. It helps users upload academic PDF documents, extract and analyze their content, ask document-grounded questions, generate document intelligence, and discover related published research papers with DOI, citation, abstract, and open-access links.

The project was initially prototyped with local AI models through **Ollama**, but local response generation was slow for practical use. The system was later migrated to a faster and more production-friendly architecture using **Groq API** for LLM responses and **sentence-transformers** for embeddings.

---

## Project Overview

ScholarMind is designed for students, researchers, thesis writers, and academic project developers who need a structured way to understand and analyze research documents.

Instead of simply reading a PDF manually, users can upload a paper and interact with it through an intelligent research workspace. The system extracts text, chunks the document, generates vector embeddings, stores searchable knowledge in ChromaDB, and uses Retrieval-Augmented Generation to answer user questions with source references.

The platform also provides a research-focused literature discovery feature that finds related published papers from global scholarly sources using OpenAlex.

---

## Key Features

### Document Upload and Processing

* Upload academic PDF documents
* Extract text from PDF files
* Create page-aware and source-aware document chunks
* Store document chunks in the database
* Generate vector embeddings for semantic search
* Store searchable vectors using ChromaDB
* Track real-time upload and processing progress

### AI-Powered Document Chat

* Ask questions directly from uploaded documents
* Retrieval-Augmented Generation based answer system
* Source-grounded answers with citation references
* Streaming AI responses
* Persistent per-document chat history
* Source preview and relevance indicators

### Document Intelligence

* Automatic document type detection
* Document profile generation
* Section-wise summaries
* Key points extraction
* Source coverage analysis
* Intelligence panel for structured academic understanding

### One-Click Academic Tools

ScholarMind includes one-click document tools for:

* Document Summary
* Main Theme
* Objectives
* Problem Statement
* Methodology / Approach
* System Design
* Implementation
* Testing and Results
* Research Gap
* Limitations
* Future Scope
* Thesis Ideas
* Presentation Points
* Viva Questions

### Related Research Literature Discovery

* Generate related published papers for an uploaded document
* Search global scholarly metadata using OpenAlex
* Display related research in a separate right-side interface
* Show title, authors, year, venue, DOI, citations, abstract, and open-access links
* Copy paper details
* Open original source links
* Open available PDF links
* Clear and regenerate related literature recommendations

### Global Scholar Search

* Search academic papers by topic or keyword
* Filter by publication year range
* Limit result count
* Enable open-access only search
* View DOI, citation count, venue, abstract, and PDF links

### Document Management

* Select previous uploaded documents
* Rename documents
* Delete documents
* Clear chat history
* Rebuild document intelligence
* Export chat history as DOCX
* Export document intelligence as DOCX
* Clear related literature

---

## System Architecture

ScholarMind follows a full-stack architecture:

```text
Frontend: React + Vite
        ↓
Backend API: Django REST Framework
        ↓
Document Processing: PDF extraction + chunking
        ↓
Embedding Layer: sentence-transformers
        ↓
Vector Store: ChromaDB
        ↓
LLM Layer: Groq API
        ↓
External Research Data: OpenAlex API
```

---

## AI Architecture Evolution

The project originally started with a local AI setup using **Ollama**. While Ollama was useful for local experimentation, it created practical limitations:

* Slow response generation
* Heavy local resource usage
* Less suitable for smooth user experience
* Difficult to scale for a polished research assistant workflow

To improve performance, the architecture was upgraded:

```text
Old approach:
Ollama local LLM + local embeddings

Current approach:
Groq API for LLM responses
sentence-transformers for embeddings
ChromaDB for vector search
OpenAlex for scholarly literature discovery
```

This migration improved response speed, reduced local LLM dependency, and made the system more suitable for future deployment.

---

## Tech Stack

### Frontend

* React
* Vite
* Tailwind CSS
* Axios
* Lucide React
* React Markdown
* Remark GFM

### Backend

* Python
* Django
* Django REST Framework
* ChromaDB
* sentence-transformers
* Groq API
* OpenAlex API
* PDF processing libraries
* DOCX export support

### AI and Search

* Groq LLM API
* sentence-transformers embedding model
* ChromaDB vector database
* Retrieval-Augmented Generation
* OpenAlex scholarly search API

---

## Project Structure

```text
scholarmind/
├── backend/
│   ├── papers/
│   │   ├── services/
│   │   │   ├── llm_service.py
│   │   │   ├── embedding_service.py
│   │   │   ├── scholar_service.py
│   │   │   ├── related_paper_service.py
│   │   │   └── vector_service.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── scholarmind_backend/
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   │   └── ScholarSearchPanel.jsx
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── .env.example
│
├── .gitignore
└── README.md
```

---

## Local Setup Guide

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/scholarmind.git
cd scholarmind
```

---

## Backend Setup

### 2. Go to Backend Folder

```bash
cd backend
```

### 3. Create Virtual Environment

```bash
python -m venv venv
```

### 4. Activate Virtual Environment

For Windows PowerShell:

```bash
venv\Scripts\activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Create Environment File

Copy the example environment file:

```bash
copy .env.example .env
```

Then update `.env` with your real values.

Example:

```env
GROQ_API_KEY=your_groq_api_key_here
LLM_PROVIDER=groq
GROQ_MODEL=llama-3.3-70b-versatile

EMBEDDING_PROVIDER=sentence-transformers
SENTENCE_TRANSFORMER_MODEL=sentence-transformers/all-MiniLM-L6-v2

LLM_TEMPERATURE=0.2
EMBEDDING_BATCH_SIZE=16
RAG_TOP_K=6

OPENALEX_MAILTO=your_email@example.com
SCHOLAR_SEARCH_DEFAULT_LIMIT=10
SCHOLAR_SEARCH_MAX_LIMIT=25
SCHOLAR_SEARCH_TIMEOUT=20
```

### 7. Run Database Migrations

```bash
python manage.py migrate
```

### 8. Start Backend Server

```bash
python manage.py runserver
```

Backend will run at:

```text
http://127.0.0.1:8000
```

API base URL:

```text
http://127.0.0.1:8000/api
```

---

## Frontend Setup

### 9. Go to Frontend Folder

Open a new terminal:

```bash
cd frontend
```

### 10. Install Frontend Dependencies

```bash
npm install
```

### 11. Create Frontend Environment File

```bash
copy .env.example .env
```

Example frontend `.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

### 12. Start Frontend Server

```bash
npm run dev
```

Frontend will run at:

```text
http://localhost:5173
```

---

## Important Environment Files

This project uses environment variables for API keys and configuration.

The real environment files are not committed to GitHub:

```text
backend/.env
frontend/.env
```

Only example files are included:

```text
backend/.env.example
frontend/.env.example
```

---

## Security Notice

Never commit the following files or folders to GitHub:

```text
.env
backend/.env
frontend/.env
backend/db.sqlite3
backend/media/
backend/chroma_db/
backend/venv/
frontend/node_modules/
frontend/dist/
```

API keys such as `GROQ_API_KEY` must always remain private.

---

## Core Backend API Features

The backend provides APIs for:

```text
Document upload
Document listing
Document detail
Document rename
Document delete
Chat history
Streaming document chat
Document intelligence
Document intelligence reprocessing
Related literature generation
Related literature clearing
Global scholar search
DOCX export
System warmup
Upload progress tracking
```

---

## Related Literature Workflow

The related literature system works as follows:

```text
Uploaded paper
    ↓
Document intelligence generated
    ↓
Search query generated from document title/profile/key points
    ↓
OpenAlex API search
    ↓
Related papers normalized
    ↓
Results saved in database
    ↓
Frontend displays results in a separate right-side research panel
```

Each related paper may include:

* Title
* Authors
* Publication year
* Venue
* DOI
* Source URL
* PDF URL
* Open-access status
* Citation count
* Abstract
* Research concepts
* Explanation of why it is related

---

## Current Deployment Plan

The project is planned for a split deployment:

```text
Frontend → Vercel
Backend  → VPS
```

This approach is preferred because the backend uses PDF processing, local file storage, ChromaDB, and persistent document data. A VPS gives more control and avoids free hosting cold-start delays.

Recommended production direction:

```text
Frontend: Vercel
Backend: Ubuntu VPS
Server: Nginx + Gunicorn
Database: PostgreSQL in future
File storage: VPS disk or cloud storage in future
Vector DB: ChromaDB on VPS or hosted vector DB in future
```

---

## Development Status

ScholarMind is currently in active development.

Completed major modules:

* PDF upload and extraction
* Document chunking
* Embedding generation
* ChromaDB vector indexing
* RAG chat
* Groq migration
* Document intelligence
* Chat history
* DOCX export
* Global scholar search
* Related research literature system
* Right-side related literature interface
* Floating research action dock

Planned improvements:

* Full production deployment
* VPS backend setup
* PostgreSQL support
* Cloud file storage support
* Literature review matrix
* Saved important papers
* Citation export in APA, IEEE, and BibTeX
* Paper comparison system
* Research gap generator
* Thesis proposal generator

---

## Why ScholarMind Matters

Academic research usually requires reading long documents, identifying research gaps, understanding methodology, comparing related work, and preparing summaries or presentation points. ScholarMind brings these tasks into one research-focused workspace.

The system is not only a PDF chatbot. It is designed as a structured academic assistant that combines:

```text
Document understanding
+
Source-grounded question answering
+
Research literature discovery
+
Academic workflow support
```

---

## Author

Developed by Md. Shahmul Islam.

---

## License

No license has been added yet. Add a license before making the project open for public reuse.
