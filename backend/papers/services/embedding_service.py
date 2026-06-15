from math import ceil
from threading import Lock

from sentence_transformers import SentenceTransformer

from .config import (
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_PROVIDER,
    SENTENCE_TRANSFORMER_MODEL,
)


_embedding_model = None
_embedding_lock = Lock()


def get_embedding_model():
    global _embedding_model

    if EMBEDDING_PROVIDER != "sentence-transformers":
        raise ValueError(
            f"Unsupported EMBEDDING_PROVIDER: {EMBEDDING_PROVIDER}. "
            "Use EMBEDDING_PROVIDER=sentence-transformers"
        )

    if _embedding_model is None:
        with _embedding_lock:
            if _embedding_model is None:
                _embedding_model = SentenceTransformer(
                    SENTENCE_TRANSFORMER_MODEL
                )

    return _embedding_model


def normalize_text(text):
    if text is None:
        return ""

    return str(text).replace("\x00", " ").strip()


def generate_embedding(text):
    clean_text = normalize_text(text)

    if not clean_text:
        clean_text = "empty"

    model = get_embedding_model()

    vector = model.encode(
        clean_text,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    return vector.astype(float).tolist()


def generate_embeddings(texts, progress_callback=None):
    if not texts:
        return []

    clean_texts = []

    for text in texts:
        clean = normalize_text(text)
        clean_texts.append(clean if clean else "empty")

    model = get_embedding_model()

    all_vectors = []
    total_batches = ceil(len(clean_texts) / max(EMBEDDING_BATCH_SIZE, 1))

    for batch_index, start in enumerate(
        range(0, len(clean_texts), EMBEDDING_BATCH_SIZE),
        start=1
    ):
        batch_texts = clean_texts[start:start + EMBEDDING_BATCH_SIZE]

        if progress_callback:
            progress_callback(batch_index, total_batches, "started")

        vectors = model.encode(
            batch_texts,
            batch_size=EMBEDDING_BATCH_SIZE,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        all_vectors.extend(
            [vector.astype(float).tolist() for vector in vectors]
        )

        if progress_callback:
            progress_callback(batch_index, total_batches, "completed")

    return all_vectors


def warmup_embedding_model():
    test_vector = generate_embedding("ScholarMind embedding warmup test.")

    return {
        "status": "ready",
        "provider": EMBEDDING_PROVIDER,
        "model": SENTENCE_TRANSFORMER_MODEL,
        "dimension": len(test_vector),
    }