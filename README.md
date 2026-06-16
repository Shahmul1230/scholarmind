# ScholarMind

**ScholarMind** is a full-stack AI-powered academic research assistant that helps users upload research papers, analyze documents, ask questions from uploaded papers, generate document intelligence, and discover related published literature.

The project is built as a production-ready portfolio application using **React**, **Django REST Framework**, **Groq LLM**, **Sentence Transformers**, **ChromaDB**, and **OpenAlex**.

---

## Live Demo

* **Frontend:** https://scholarmind-zeta.vercel.app
* **Backend API:** https://appi.pixelstack.cloud/api

---

## Project Overview

ScholarMind is designed for students, researchers, thesis writers, and academic professionals who need a smarter way to interact with research papers.

Instead of only reading a PDF manually, users can upload a document and ask questions directly from the paper. The system extracts text, creates searchable chunks, generates AI-based answers with source references, and provides research-oriented insights such as methodology, objectives, limitations, findings, and related literature.

---

## Key Features

### Document Upload and Processing

* Upload academic PDF documents.
* Extract text from uploaded papers.
* Create structured chunks from document content.
* Store processed document data for later use.
* Support document-based chat and analysis.

### AI Research Assistant

* Ask questions based on uploaded papers.
* Generate answers using document context.
* Retrieve relevant source chunks for answer grounding.
* Maintain chat history for each uploaded paper.
* Provide source-aware academic responses.

### Document Intelligence

ScholarMind can generate structured analysis from a paper, including:

* Research objectives
* Problem statement
* Methodology or approach
* System design or implementation details
* Testing and results
* Key findings
* Limitations
* Future work

### Related Literature Discovery

* Search related academic papers using OpenAlex.
* Generate related literature based on uploaded document context.
* Show titles, authors, publication year, DOI, citation count, and open-access links.
* Help users discover relevant published studies for literature review.

### Export Features

* Export chat history as a DOCX file.
* Export document intelligence report as a DOCX file.
* Useful for academic notes, assignments, and research documentation.

### Document Management

* Rename uploaded documents.
* Delete documents.
* Clear chat history.
* Reprocess analysis.
* Manage multiple research papers from the sidebar.

---

## Tech Stack

### Frontend

* React
* Vite
* Tailwind CSS
* Axios
* Lucide React
* Vercel deployment

### Backend

* Python
* Django
* Django REST Framework
* Gunicorn
* Nginx
* Hostinger VPS deployment

### AI and NLP

* Groq API for LLM responses
* Sentence Transformers for embeddings
* ChromaDB for vector storage
* OpenAlex API for scholarly paper discovery

### Document Processing

* PyPDF
* Python DOCX
* OCR-supporting server packages
* Static and media file handling through Django/Nginx

---

## System Architecture

```text
User Browser
    |
    |  React Frontend
    v
Vercel Deployment
    |
    |  API Requests
    v
Hostinger VPS Backend
    |
    |  Django REST API
    v
Document Processing + RAG Pipeline
    |
    |-- PDF Text Extraction
    |-- Chunk Creation
    |-- Embedding Generation
    |-- ChromaDB Vector Search
    |-- Groq LLM Answer Generation
    |-- OpenAlex Related Paper Search
```

---

## Deployment Architecture

The project is deployed using a separated frontend-backend architecture.

```text
Frontend:
https://scholarmind-zeta.vercel.app

Backend:
https://appi.pixelstack.cloud/api

Backend Server:
Hostinger VPS + Nginx + Gunicorn + Django
```

This deployment structure keeps the frontend lightweight and allows the backend to run heavier AI components such as Sentence Transformers and ChromaDB on a VPS.

---

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Shahmul1230/scholarmind.git
cd scholarmind
```

---

## Backend Setup

### 2. Create and Activate Virtual Environment

```bash
cd backend
python -m venv venv
```

For Windows:

```bash
venv\Scripts\activate
```

For Linux/macOS:

```bash
source venv/bin/activate
```

### 3. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create `.env` File

Create a `.env` file inside the `backend` folder.

```env
SECRET_KEY=your_django_secret_key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
CSRF_TRUSTED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

GROQ_API_KEY=your_groq_api_key
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

### 5. Run Database Migrations

```bash
python manage.py migrate
```

### 6. Start Backend Server

```bash
python manage.py runserver
```

Backend will run at:

```text
http://127.0.0.1:8000/api
```

---

## Frontend Setup

### 7. Install Frontend Dependencies

Open a new terminal:

```bash
cd frontend
npm install
```

### 8. Create Frontend Environment File

Create a `.env` file inside the `frontend` folder.

For local development:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

For production:

```env
VITE_API_BASE_URL=https://appi.pixelstack.cloud/api
```

### 9. Start Frontend Development Server

```bash
npm run dev
```

Frontend will run at:

```text
http://localhost:5173
```

---

## Production Deployment

### Frontend Deployment

The frontend is deployed on Vercel.

Required Vercel environment variable:

```env
VITE_API_BASE_URL=https://appi.pixelstack.cloud/api
```

Vercel settings:

```text
Framework Preset: Vite
Root Directory: frontend
Build Command: npm run build
Output Directory: dist
Install Command: npm install
```

### Backend Deployment

The backend is deployed on a Hostinger VPS using:

* Django
* Gunicorn
* Nginx
* Certbot SSL
* Systemd service

Backend domain:

```text
https://appi.pixelstack.cloud/api
```

---

## Backend VPS Service

ScholarMind backend runs as a systemd service:

```bash
systemctl status scholarmind
```

Restart backend:

```bash
systemctl restart scholarmind
```

View backend logs:

```bash
journalctl -u scholarmind -f
```

---

## Future Update Workflow

### Update Code Locally

```bash
git add .
git commit -m "Update ScholarMind"
git push
```

### Update Backend on VPS

```bash
ssh root@your_vps_ip
cd /opt/scholarmind
git pull
cd backend
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
systemctl restart scholarmind
```

The frontend automatically redeploys on Vercel after pushing changes to GitHub.

---

## Security Notes

* `.env` files are not committed to GitHub.
* API keys and secret keys must be stored only in environment variables.
* The Groq API key should never be exposed in frontend code.
* Production backend uses `DEBUG=False`.
* CORS and CSRF trusted origins should only include trusted frontend URLs.

---

## Project Structure

```text
scholarmind/
├── backend/
│   ├── papers/
│   ├── scholarmind_backend/
│   ├── media/
│   ├── staticfiles/
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example
│
├── README.md
├── .gitignore
└── Dockerfile
```

---

## Current Status

ScholarMind is successfully deployed with:

* React frontend on Vercel
* Django backend on Hostinger VPS
* HTTPS-enabled backend API
* Groq-powered AI responses
* Document upload and analysis
* Related literature discovery
* DOCX export support

---

## Planned Improvements

* User authentication
* PostgreSQL database migration
* Cloud file storage
* Advanced citation formatting
* Multi-user document workspace
* Better analytics dashboard
* Admin panel for uploaded documents
* Improved research report generation

---

## Author

**Shahmul Islam**

GitHub: https://github.com/Shahmul1230

---

## License

This project is currently developed as a personal academic and portfolio project.
License information may be added in the future.
