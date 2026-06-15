import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent

load_dotenv(BACKEND_DIR / ".env")
load_dotenv(PROJECT_ROOT / ".env")


# =========================
# LLM Provider: Groq
# =========================
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").strip().lower()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()

LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))


# =========================
# Embedding Provider: Sentence Transformers
# =========================
EMBEDDING_PROVIDER = os.getenv(
    "EMBEDDING_PROVIDER",
    "sentence-transformers"
).strip().lower()

SENTENCE_TRANSFORMER_MODEL = os.getenv(
    "SENTENCE_TRANSFORMER_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2"
).strip()

EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "16"))


# =========================
# RAG Config
# =========================
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "6"))
MAX_CONTEXT_CHARS_PER_CHUNK = int(os.getenv("MAX_CONTEXT_CHARS_PER_CHUNK", "1100"))

REPORT_FIRST_CHUNKS = int(os.getenv("REPORT_FIRST_CHUNKS", "4"))
REPORT_LAST_CHUNKS = int(os.getenv("REPORT_LAST_CHUNKS", "4"))
REPORT_MAX_TOTAL_SOURCES = int(os.getenv("REPORT_MAX_TOTAL_SOURCES", "12"))

ANALYSIS_MAX_SECTIONS = int(os.getenv("ANALYSIS_MAX_SECTIONS", "10"))
ANALYSIS_MAX_CHUNKS_PER_SECTION = int(os.getenv("ANALYSIS_MAX_CHUNKS_PER_SECTION", "4"))
ANALYSIS_MAX_CHARS_PER_SECTION = int(os.getenv("ANALYSIS_MAX_CHARS_PER_SECTION", "4500"))
ANALYSIS_PROFILE_MAX_CHARS = int(os.getenv("ANALYSIS_PROFILE_MAX_CHARS", "6000"))
ANALYSIS_SUMMARY_MAX_CHARS_FOR_RAG = int(
    os.getenv("ANALYSIS_SUMMARY_MAX_CHARS_FOR_RAG", "3500")
)

# =========================
# Scholar Search Config
# =========================
OPENALEX_BASE_URL = os.getenv(
    "OPENALEX_BASE_URL",
    "https://api.openalex.org"
).strip()

OPENALEX_MAILTO = os.getenv("OPENALEX_MAILTO", "").strip()

SCHOLAR_SEARCH_DEFAULT_LIMIT = int(
    os.getenv("SCHOLAR_SEARCH_DEFAULT_LIMIT", "10")
)

SCHOLAR_SEARCH_MAX_LIMIT = int(
    os.getenv("SCHOLAR_SEARCH_MAX_LIMIT", "25")
)

SCHOLAR_SEARCH_TIMEOUT = int(
    os.getenv("SCHOLAR_SEARCH_TIMEOUT", "20")
)