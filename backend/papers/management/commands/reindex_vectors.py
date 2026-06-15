from django.core.management.base import BaseCommand

from papers.models import Paper, PaperChunk
from papers.services.config import EMBEDDING_BATCH_SIZE
from papers.services.embedding_service import generate_embeddings
from papers.services.vector_service import add_chunks_to_vector_db


class Command(BaseCommand):
    help = "Rebuild ChromaDB vectors for existing PaperChunk rows."

    def handle(self, *args, **options):
        papers = Paper.objects.filter(status="ready").order_by("id")

        if not papers.exists():
            self.stdout.write(self.style.WARNING("No ready papers found."))
            return

        total_chunks_indexed = 0

        for paper in papers:
            chunks = list(
                PaperChunk.objects.filter(paper=paper)
                .exclude(content__isnull=True)
                .order_by("chunk_index")
            )

            if not chunks:
                self.stdout.write(
                    self.style.WARNING(
                        f"No chunks found for paper {paper.id}: {paper.title}"
                    )
                )
                continue

            self.stdout.write(
                self.style.NOTICE(
                    f"Reindexing paper {paper.id}: {paper.title} ({len(chunks)} chunks)"
                )
            )

            for start in range(0, len(chunks), EMBEDDING_BATCH_SIZE):
                batch = chunks[start:start + EMBEDDING_BATCH_SIZE]

                contents = [chunk.content or "" for chunk in batch]
                embeddings = generate_embeddings(contents)

                vector_ids = []
                metadatas = []

                for chunk in batch:
                    if not chunk.vector_id:
                        chunk.vector_id = f"paper_{paper.id}_chunk_{chunk.chunk_index}"
                        chunk.save(update_fields=["vector_id"])

                    vector_ids.append(chunk.vector_id)

                    metadatas.append({
                        "paper_id": paper.id,
                        "paper_title": paper.title,
                        "chunk_index": chunk.chunk_index,
                        "page_number": chunk.page_number,
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                        "section_title": chunk.section_title or "Unknown",
                    })

                add_chunks_to_vector_db(
                    vector_ids=vector_ids,
                    contents=contents,
                    embeddings=embeddings,
                    metadatas=metadatas,
                )

                total_chunks_indexed += len(batch)

                self.stdout.write(
                    f"  Indexed {min(start + EMBEDDING_BATCH_SIZE, len(chunks))}/{len(chunks)}"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Reindex complete. Total chunks indexed: {total_chunks_indexed}"
            )
        )