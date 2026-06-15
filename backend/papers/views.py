import json
import os
import requests
import json
from django.http import StreamingHttpResponse
from .services.rag_service import build_rag_payload, finalize_sources_for_answer
from .services.llm_service import stream_llm_answer
from .services.scholar_service import search_openalex_works
from django.http import StreamingHttpResponse, JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status

from .services.llm_service import warmup_llm
from .services.embedding_service import warmup_embedding_model

from .models import Paper, PaperChunk, ChatMessage, DocumentAnalysis, RelatedPaper
from .serializers import (
    PaperSerializer,
    PaperChunkSerializer,
    ChatMessageSerializer,
    DocumentAnalysisSerializer,
    RelatedPaperSerializer,
)

from .services.related_paper_service import generate_related_papers_for_document
from .services.pdf_service import extract_text_from_pdf
from .services.chunk_service import chunk_text
from .services.embedding_service import generate_embedding, generate_embeddings, warmup_embedding_model
from .services.vector_service import (
    add_chunks_to_vector_db,
    search_similar_chunks,
    delete_paper_vectors,
)
from .services.rag_service import (
    ask_question_from_paper,
    build_rag_payload,
    finalize_sources_for_answer,
)

from .services.llm_service import generate_llm_answer, stream_llm_answer, warmup_llm
from .services.document_analysis_service import analyze_document
from .services.progress_service import (
    init_progress,
    update_progress,
    complete_progress,
    fail_progress,
    get_progress,
)

from .services.export_service import (
    build_chat_history_docx,
    build_analysis_docx,
    safe_export_filename,
)


@api_view(["GET"])
def health_check(request):
    return Response({
        "message": "ScholarMind backend is connected successfully!"
    })


@api_view(["GET"])
def warmup_system(request):
    try:
        llm_status = warmup_llm()
        embedding_status = warmup_embedding_model()

        return Response({
            "status": "ready",
            "llm": llm_status,
            "embedding": embedding_status,
        })

    except Exception as e:
        return Response(
            {
                "status": "failed",
                "error": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(["GET"])
def upload_progress(request, upload_id):
    return Response(get_progress(upload_id))

@api_view(["POST"])
def global_scholar_search(request):
    query = request.data.get("query", "").strip()
    limit = request.data.get("limit", None)
    from_year = request.data.get("from_year", None)
    to_year = request.data.get("to_year", None)
    open_access_only = request.data.get("open_access_only", False)

    if not query:
        return Response(
            {"error": "Search query is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        results = search_openalex_works(
            query=query,
            limit=limit,
            from_year=from_year,
            to_year=to_year,
            open_access_only=open_access_only,
        )

        return Response(results)

    except requests.exceptions.Timeout:
        return Response(
            {
                "error": "Scholar search timed out.",
                "details": "OpenAlex did not respond within the configured timeout.",
            },
            status=status.HTTP_504_GATEWAY_TIMEOUT
        )

    except requests.exceptions.RequestException as e:
        return Response(
            {
                "error": "Scholar search request failed.",
                "details": str(e),
            },
            status=status.HTTP_502_BAD_GATEWAY
        )

    except Exception as e:
        return Response(
            {
                "error": "Scholar search failed.",
                "details": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(["GET"])
def paper_list(request):
    papers = Paper.objects.all().order_by("-uploaded_at")

    serializer = PaperSerializer(
        papers,
        many=True,
        context={"request": request}
    )

    return Response(serializer.data)


@api_view(["GET"])
def paper_detail(request, paper_id):
    try:
        paper = Paper.objects.get(id=paper_id)
    except Paper.DoesNotExist:
        return Response(
            {"error": "Paper not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = PaperSerializer(
        paper,
        context={"request": request}
    )

    return Response(serializer.data)


@api_view(["PATCH"])
def rename_paper(request, paper_id):
    try:
        paper = Paper.objects.get(id=paper_id)
    except Paper.DoesNotExist:
        return Response(
            {"error": "Paper not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    title = request.data.get("title", "").strip()

    if not title:
        return Response(
            {"error": "New title is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(title) > 255:
        return Response(
            {"error": "Title is too long. Maximum 255 characters allowed."},
            status=status.HTTP_400_BAD_REQUEST
        )

    paper.title = title
    paper.save()

    serializer = PaperSerializer(
        paper,
        context={"request": request}
    )

    return Response({
        "message": "Document renamed successfully.",
        "paper": serializer.data,
    })


@api_view(["DELETE"])
def delete_paper(request, paper_id):
    try:
        paper = Paper.objects.get(id=paper_id)
    except Paper.DoesNotExist:
        return Response(
            {"error": "Paper not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    paper_title = paper.title
    file_path = paper.file.path if paper.file else None

    vector_delete_result = delete_paper_vectors(paper.id)

    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception as file_error:
        return Response(
            {
                "error": "Document vectors were handled, but file deletion failed.",
                "details": str(file_error),
                "vector_delete_result": vector_delete_result,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    paper.delete()

    return Response({
        "message": "Document deleted successfully.",
        "deleted_document": paper_title,
        "vector_delete_result": vector_delete_result,
    })


@api_view(["POST", "DELETE"])
def clear_chat_history(request, paper_id):
    try:
        paper = Paper.objects.get(id=paper_id)
    except Paper.DoesNotExist:
        return Response(
            {"error": "Paper not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    deleted_count, _ = ChatMessage.objects.filter(paper=paper).delete()

    serializer = PaperSerializer(
        paper,
        context={"request": request}
    )

    return Response({
        "message": "Chat history cleared successfully.",
        "deleted_messages": deleted_count,
        "paper": serializer.data,
    })

@api_view(["GET"])
def export_chat_history_docx(request, paper_id):
    try:
        paper = Paper.objects.get(id=paper_id)
    except Paper.DoesNotExist:
        return Response(
            {"error": "Paper not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    try:
        docx_bytes = build_chat_history_docx(paper)
        filename = safe_export_filename(paper.title, "chat_history")

        response = HttpResponse(
            docx_bytes,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response

    except Exception as e:
        return Response(
            {
                "error": "Chat export failed.",
                "details": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
def export_analysis_docx(request, paper_id):
    try:
        paper = Paper.objects.get(id=paper_id)
    except Paper.DoesNotExist:
        return Response(
            {"error": "Paper not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    try:
        docx_bytes = build_analysis_docx(paper)
        filename = safe_export_filename(paper.title, "document_intelligence")

        response = HttpResponse(
            docx_bytes,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response

    except ValueError as e:
        return Response(
            {
                "error": "Document intelligence export failed.",
                "details": str(e),
            },
            status=status.HTTP_404_NOT_FOUND
        )

    except Exception as e:
        return Response(
            {
                "error": "Document intelligence export failed.",
                "details": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(["POST"])
def reprocess_document_analysis(request, paper_id):
    try:
        paper = Paper.objects.get(id=paper_id)
    except Paper.DoesNotExist:
        return Response(
            {"error": "Paper not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    if paper.status != "ready":
        return Response(
            {
                "error": "Only ready documents can be reprocessed.",
                "current_status": paper.status,
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    chunk_count = PaperChunk.objects.filter(paper=paper).count()

    if chunk_count == 0:
        return Response(
            {
                "error": "No chunks found for this document. Re-upload the PDF instead."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        analysis = analyze_document(
            paper=paper,
            progress_callback=None,
        )

        serializer = DocumentAnalysisSerializer(analysis)

        return Response({
            "message": "Document intelligence rebuilt successfully.",
            "analysis": serializer.data,
        })

    except Exception as e:
        return Response(
            {
                "error": "Document intelligence reprocessing failed.",
                "details": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
def paper_chunks(request, paper_id):
    try:
        paper = Paper.objects.get(id=paper_id)
    except Paper.DoesNotExist:
        return Response(
            {"error": "Paper not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    chunks = paper.chunks.all().order_by("chunk_index")
    serializer = PaperChunkSerializer(chunks, many=True)

    return Response(serializer.data)


@api_view(["GET"])
def paper_analysis(request, paper_id):
    try:
        analysis = DocumentAnalysis.objects.get(paper_id=paper_id)
    except DocumentAnalysis.DoesNotExist:
        return Response(
            {"error": "Document analysis not found for this paper."},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = DocumentAnalysisSerializer(analysis)
    return Response(serializer.data)

@api_view(["GET"])
def paper_related_papers(request, paper_id):
    try:
        paper = Paper.objects.get(id=paper_id)
    except Paper.DoesNotExist:
        return Response(
            {"error": "Paper not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    related = RelatedPaper.objects.filter(paper=paper)

    serializer = RelatedPaperSerializer(related, many=True)

    return Response({
        "paper_id": paper.id,
        "paper_title": paper.title,
        "count": related.count(),
        "results": serializer.data,
    })


@api_view(["POST"])
def generate_paper_related_papers(request, paper_id):
    limit = request.data.get("limit", 10)
    from_year = request.data.get("from_year", 2018)
    to_year = request.data.get("to_year", None)
    open_access_only = request.data.get("open_access_only", False)

    try:
        result = generate_related_papers_for_document(
            paper_id=paper_id,
            limit=limit,
            from_year=from_year,
            to_year=to_year,
            open_access_only=open_access_only,
        )

        serializer = RelatedPaperSerializer(result["items"], many=True)

        return Response({
            "message": "Related literature generated successfully.",
            "paper_id": result["paper"].id,
            "paper_title": result["paper"].title,
            "search_query": result["search_query"],
            "count": result["count"],
            "results": serializer.data,
        })

    except ValueError as e:
        return Response(
            {
                "error": "Related literature generation failed.",
                "details": str(e),
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    except Exception as e:
        return Response(
            {
                "error": "Related literature generation failed.",
                "details": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["DELETE"])
def clear_paper_related_papers(request, paper_id):
    try:
        paper = Paper.objects.get(id=paper_id)
    except Paper.DoesNotExist:
        return Response(
            {"error": "Paper not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    deleted_count, _ = RelatedPaper.objects.filter(paper=paper).delete()

    return Response({
        "message": "Related literature cleared successfully.",
        "deleted_count": deleted_count,
    })

@api_view(["GET"])
def semantic_search(request, paper_id):
    query = request.GET.get("q")

    if not query:
        return Response(
            {"error": "Query parameter 'q' is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        paper = Paper.objects.get(id=paper_id)
    except Paper.DoesNotExist:
        return Response(
            {"error": "Paper not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    try:
        query_embedding = generate_embedding(query)

        results = search_similar_chunks(
            query_embedding=query_embedding,
            paper_id=paper.id,
            top_k=5
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        matched_chunks = []

        for index, (doc, meta, distance) in enumerate(
            zip(documents, metadatas, distances),
            start=1
        ):
            meta = meta or {}

            matched_chunks.append({
                "source_id": f"S{index}",
                "content": doc,
                "paper_id": meta.get("paper_id"),
                "chunk_index": meta.get("chunk_index"),
                "page_number": meta.get("page_number"),
                "start_line": meta.get("start_line"),
                "end_line": meta.get("end_line"),
                "section_title": meta.get("section_title") or "Unknown",
                "distance": distance,
            })

        return Response({
            "query": query,
            "paper_id": paper.id,
            "matches": matched_chunks,
        })

    except Exception as e:
        return Response(
            {
                "error": "Semantic search failed.",
                "details": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def chat_with_paper(request, paper_id):
    question = request.data.get("question")

    if not question:
        return Response(
            {"error": "Question is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        paper = Paper.objects.get(id=paper_id)
    except Paper.DoesNotExist:
        return Response(
            {"error": "Paper not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    try:
        ChatMessage.objects.create(
            paper=paper,
            role="user",
            message=question,
            sources=[]
        )

        rag_result = ask_question_from_paper(
            paper_id=paper.id,
            question=question
        )

        answer = rag_result["answer"]
        sources = rag_result["sources"]

        ChatMessage.objects.create(
            paper=paper,
            role="assistant",
            message=answer,
            sources=sources
        )

        return Response({
            "question": question,
            "answer": answer,
            "sources": sources,
        })

    except Exception as e:
        return Response(
            {
                "error": "RAG chat failed.",
                "details": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def chat_with_paper_stream(request, paper_id):
    question = request.data.get("question", "").strip()

    if not question:
        return Response(
            {"error": "Question is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        paper = Paper.objects.get(id=paper_id)
    except Paper.DoesNotExist:
        return Response(
            {"error": "Paper not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    if paper.status != "ready":
        return Response(
            {
                "error": "Paper is not ready yet.",
                "current_status": paper.status,
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    ChatMessage.objects.create(
        paper=paper,
        role="user",
        message=question,
        sources=[],
    )

    rag_payload = build_rag_payload(
        paper_id=paper.id,
        question=question,
    )

    raw_sources = rag_payload.get("sources", [])
    prompt = rag_payload.get("prompt", "")

    def event_stream():
        answer_parts = []

        try:
            yield f"data: {json.dumps({'type': 'sources', 'sources': raw_sources})}\n\n"

            for token in stream_llm_answer(prompt):
                answer_parts.append(token)
                yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"

            final_answer = "".join(answer_parts).strip()

            final_sources = finalize_sources_for_answer(
                answer=final_answer,
                sources=raw_sources,
                question=question,
            )

            ChatMessage.objects.create(
                paper=paper,
                role="assistant",
                message=final_answer,
                sources=final_sources,
            )

            yield f"data: {json.dumps({'type': 'sources', 'sources': final_sources})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    response = StreamingHttpResponse(
        event_stream(),
        content_type="text/event-stream",
    )

    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"

    return response


@api_view(["GET"])
def chat_history(request, paper_id):
    try:
        paper = Paper.objects.get(id=paper_id)
    except Paper.DoesNotExist:
        return Response(
            {"error": "Paper not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    messages = paper.chat_messages.all().order_by("created_at")
    serializer = ChatMessageSerializer(messages, many=True)

    return Response(serializer.data)


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def upload_paper(request):
    file = request.FILES.get("file")
    title = request.data.get("title")
    upload_id = request.data.get("upload_id")

    init_progress(upload_id)

    if not file:
        fail_progress(upload_id, "No PDF file was provided.")
        return Response(
            {"error": "No PDF file provided."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not file.name.lower().endswith(".pdf"):
        fail_progress(upload_id, "Only PDF files are allowed.")
        return Response(
            {"error": "Only PDF files are allowed."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not title:
        title = file.name.rsplit(".", 1)[0]

    update_progress(
        upload_id=upload_id,
        stage="Saving PDF",
        percent=5,
        details="Saving the uploaded PDF file to the server."
    )

    paper = Paper.objects.create(
        title=title,
        file=file,
        status="processing"
    )

    try:
        update_progress(
            upload_id=upload_id,
            stage="Extracting text",
            percent=15,
            details="Reading PDF pages. If the PDF is scanned, OCR may be used."
        )

        extracted_data = extract_text_from_pdf(paper.file.path)

        paper.extracted_text = extracted_data["text"]
        paper.total_pages = extracted_data["total_pages"]

        extraction_method = extracted_data.get("method", "unknown")
        warning = extracted_data.get("warning")

        if not paper.extracted_text:
            paper.status = "failed"
            paper.save()

            fail_progress(
                upload_id,
                "PDF uploaded, but no text could be extracted. It may be a scanned PDF and OCR may not be installed correctly."
            )

            return Response(
                {
                    "error": "PDF uploaded but no text could be extracted. It may be a scanned PDF."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        paper.save()

        update_progress(
            upload_id=upload_id,
            stage="Creating chunks",
            percent=35,
            details=f"Text extracted using {extraction_method}. Creating source-aware chunks."
        )

        chunks = chunk_text(extracted_data["pages"])

        if not chunks:
            paper.status = "failed"
            paper.save()

            fail_progress(
                upload_id,
                "PDF text was extracted, but no chunks were created."
            )

            return Response(
                {
                    "error": "PDF text was extracted, but no chunks were created."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        update_progress(
            upload_id=upload_id,
            stage="Saving chunks",
            percent=45,
            details=f"Saving {len(chunks)} chunks with page and line metadata."
        )

        vector_ids = []
        contents = []
        metadatas = []

        for chunk in chunks:
            vector_id = f"paper_{paper.id}_chunk_{chunk['chunk_index']}"

            page_number = chunk.get("page_number")
            start_line = chunk.get("start_line")
            end_line = chunk.get("end_line")
            section_title = chunk.get("section_title") or "Unknown"

            paper_chunk = PaperChunk.objects.create(
                paper=paper,
                chunk_index=chunk["chunk_index"],
                content=chunk["content"],
                page_number=page_number,
                start_line=start_line,
                end_line=end_line,
                section_title=section_title,
                vector_id=vector_id
            )

            vector_ids.append(vector_id)
            contents.append(paper_chunk.content)

            metadatas.append({
                "paper_id": paper.id,
                "chunk_index": paper_chunk.chunk_index,
                "page_number": page_number or 0,
                "start_line": start_line or 0,
                "end_line": end_line or 0,
                "section_title": section_title,
            })

        update_progress(
            upload_id=upload_id,
            stage="Generating embeddings",
            percent=55,
            details=f"Generating embeddings for {len(contents)} chunks."
        )

        def embedding_progress(batch_index, total_batches, status):
            percent = 55 + int((batch_index / max(total_batches, 1)) * 25)

            update_progress(
                upload_id=upload_id,
                stage="Generating embeddings",
                percent=percent,
                details=f"Embedding batch {batch_index} of {total_batches} {status}."
            )

        embeddings = generate_embeddings(
            contents,
            progress_callback=embedding_progress
        )

        if len(embeddings) != len(contents):
            raise ValueError(
                f"Embedding count mismatch. Expected {len(contents)}, got {len(embeddings)}."
            )

        update_progress(
            upload_id=upload_id,
            stage="Indexing vectors",
            percent=85,
            details="Saving embeddings and source chunks into ChromaDB."
        )

        add_chunks_to_vector_db(
            vector_ids=vector_ids,
            contents=contents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        update_progress(
            upload_id=upload_id,
            stage="Building document intelligence",
            percent=88,
            details="Creating section summaries and whole-document intelligence profile."
        )

        analysis_warning = None

        try:
            def analysis_progress(stage, percent, details):
                update_progress(
                    upload_id=upload_id,
                    stage=stage,
                    percent=percent,
                    details=details
                )

            analyze_document(
                paper=paper,
                progress_callback=analysis_progress,
            )

        except Exception as analysis_error:
            analysis_warning = str(analysis_error)

            update_progress(
                upload_id=upload_id,
                stage="Document intelligence warning",
                percent=96,
                details=f"Core indexing completed, but deep analysis failed: {analysis_warning}"
            )

        update_progress(
            upload_id=upload_id,
            stage="Finalizing",
            percent=98,
            details="Finalizing document status and preparing assistant tools."
        )

        paper.status = "ready"
        paper.save()

        complete_progress(
            upload_id,
            details=analysis_warning or warning or "Document intelligence profile is ready for deep Q&A."
        )

    except Exception as e:
        paper.status = "failed"
        paper.save()

        fail_progress(upload_id, str(e))

        return Response(
            {
                "error": "PDF uploaded but processing failed.",
                "details": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    serializer = PaperSerializer(
        paper,
        context={"request": request}
    )

    return Response(
        {
            "message": "Paper uploaded, processed, indexed, analyzed, and ready successfully!",
            "paper": serializer.data,
            "upload_id": upload_id,
        },
        status=status.HTTP_201_CREATED
    )
