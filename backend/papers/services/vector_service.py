import chromadb
from django.conf import settings

CHROMA_DB_PATH = settings.BASE_DIR / "chroma_db"

client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))

collection = client.get_or_create_collection(
    name="scholarmind_papers"
)


def add_chunk_to_vector_db(vector_id, content, embedding, metadata):
    collection.upsert(
        ids=[vector_id],
        documents=[content],
        embeddings=[embedding],
        metadatas=[metadata],
    )


def add_chunks_to_vector_db(vector_ids, contents, embeddings, metadatas):
    if not vector_ids:
        return

    collection.upsert(
        ids=vector_ids,
        documents=contents,
        embeddings=embeddings,
        metadatas=metadatas,
    )


def search_similar_chunks(query_embedding, paper_id, top_k=3):
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"paper_id": paper_id},
    )

    return results


def delete_paper_vectors(paper_id):
    """
    Delete all ChromaDB vectors for one paper.
    This keeps document deletion clean.
    """

    try:
        collection.delete(
            where={"paper_id": paper_id}
        )

        return {
            "deleted": True,
            "method": "where",
            "paper_id": paper_id,
        }

    except Exception:
        try:
            existing = collection.get(
                where={"paper_id": paper_id}
            )

            ids = existing.get("ids", [])

            if ids:
                collection.delete(ids=ids)

            return {
                "deleted": True,
                "method": "ids",
                "paper_id": paper_id,
                "count": len(ids),
            }

        except Exception as e:
            return {
                "deleted": False,
                "paper_id": paper_id,
                "error": str(e),
            }