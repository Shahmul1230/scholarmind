from rest_framework import serializers
from .models import (
    Paper,
    PaperChunk,
    ChatMessage,
    DocumentAnalysis,
    RelatedPaper,
)


class PaperChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaperChunk
        fields = [
            "id",
            "paper",
            "chunk_index",
            "content",
            "page_number",
            "start_line",
            "end_line",
            "section_title",
            "vector_id",
            "created_at",
        ]


class DocumentAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentAnalysis
        fields = [
            "id",
            "paper",
            "document_type",
            "status",
            "profile",
            "section_summaries",
            "key_points",
            "source_coverage",
            "error_message",
            "created_at",
            "updated_at",
        ]


class RelatedPaperSerializer(serializers.ModelSerializer):
    class Meta:
        model = RelatedPaper
        fields = [
            "id",
            "paper",
            "source",
            "openalex_id",
            "title",
            "authors",
            "year",
            "publication_date",
            "venue",
            "doi",
            "url",
            "pdf_url",
            "open_access",
            "open_access_status",
            "work_type",
            "cited_by_count",
            "abstract",
            "concepts",
            "search_query",
            "why_related",
            "created_at",
        ]


class PaperSerializer(serializers.ModelSerializer):
    chunk_count = serializers.SerializerMethodField()
    chat_count = serializers.SerializerMethodField()
    analysis_status = serializers.SerializerMethodField()
    document_type = serializers.SerializerMethodField()
    related_papers_count = serializers.SerializerMethodField()

    class Meta:
        model = Paper
        fields = [
            "id",
            "title",
            "file",
            "extracted_text",
            "status",
            "total_pages",
            "uploaded_at",
            "chunk_count",
            "chat_count",
            "analysis_status",
            "document_type",
            "related_papers_count",
        ]

    def get_chunk_count(self, obj):
        return obj.chunks.count()

    def get_chat_count(self, obj):
        return obj.chat_messages.count()

    def get_analysis_status(self, obj):
        if hasattr(obj, "analysis"):
            return obj.analysis.status

        return "not_created"

    def get_document_type(self, obj):
        if hasattr(obj, "analysis"):
            return obj.analysis.document_type

        return "Unknown"

    def get_related_papers_count(self, obj):
        return obj.related_papers.count()


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "paper",
            "role",
            "message",
            "sources",
            "created_at",
        ]