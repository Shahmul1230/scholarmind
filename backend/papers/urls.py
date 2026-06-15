from django.urls import path
from .views import (
    health_check,
    warmup_system,
    upload_progress,

    paper_list,
    paper_detail,
    rename_paper,
    delete_paper,
    clear_chat_history,
    reprocess_document_analysis,

    paper_chunks,
    paper_analysis,
    semantic_search,

    chat_with_paper,
    chat_with_paper_stream,
    chat_history,

    export_chat_history_docx,
    export_analysis_docx,

    upload_paper,
    global_scholar_search,

    paper_related_papers,
    generate_paper_related_papers,
    clear_paper_related_papers,
)

urlpatterns = [
    path("health/", health_check, name="health_check"),
    path("system/warmup/", warmup_system, name="warmup_system"),
    path("upload-progress/<str:upload_id>/", upload_progress, name="upload_progress"),

    path("papers/", paper_list, name="paper_list"),
    path("papers/<int:paper_id>/", paper_detail, name="paper_detail"),

    path("papers/<int:paper_id>/rename/", rename_paper, name="rename_paper"),
    path("papers/<int:paper_id>/delete/", delete_paper, name="delete_paper"),
    path("papers/<int:paper_id>/clear-chat/", clear_chat_history, name="clear_chat_history"),
    path("papers/<int:paper_id>/reprocess-analysis/", reprocess_document_analysis, name="reprocess_document_analysis"),

    path("papers/<int:paper_id>/chunks/", paper_chunks, name="paper_chunks"),
    path("papers/<int:paper_id>/analysis/", paper_analysis, name="paper_analysis"),
    path("papers/<int:paper_id>/semantic-search/", semantic_search, name="semantic_search"),

    path("papers/<int:paper_id>/chat/", chat_with_paper, name="chat_with_paper"),
    path("papers/<int:paper_id>/chat-stream/", chat_with_paper_stream, name="chat_with_paper_stream"),
    path("papers/<int:paper_id>/chat-history/", chat_history, name="chat_history"),

    path("papers/<int:paper_id>/export/chat-docx/", export_chat_history_docx, name="export_chat_history_docx"),
    path("papers/<int:paper_id>/export/analysis-docx/", export_analysis_docx, name="export_analysis_docx"),
    path("papers/upload/", upload_paper, name="upload_paper"),
    path("scholar/search/", global_scholar_search, name="global_scholar_search"),
    path("papers/<int:paper_id>/related-papers/", paper_related_papers, name="paper_related_papers"),
    path("papers/<int:paper_id>/related-papers/generate/", generate_paper_related_papers, name="generate_paper_related_papers"),
    path("papers/<int:paper_id>/related-papers/clear/", clear_paper_related_papers, name="clear_paper_related_papers"),

]