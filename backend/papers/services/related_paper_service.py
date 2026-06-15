import re

from ..models import Paper, DocumentAnalysis, RelatedPaper
from .llm_service import generate_llm_answer
from .scholar_service import search_openalex_works


def clean_text(text):
    text = str(text or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text


def build_fallback_query(paper):
    title = clean_text(paper.title)

    document_type = ""

    if hasattr(paper, "analysis"):
        document_type = clean_text(paper.analysis.document_type)

    query = f"{title} {document_type}".strip()

    if not query:
        query = "research methodology academic paper"

    return query[:240]


def build_related_literature_query(paper):
    """
    Builds a concise academic search query from the uploaded paper.
    Uses Groq if available, otherwise falls back to title/document type.
    """

    fallback_query = build_fallback_query(paper)

    analysis_text = ""

    try:
        analysis = DocumentAnalysis.objects.get(paper=paper, status="ready")

        analysis_text = "\n\n".join([
            f"Document Type: {analysis.document_type}",
            f"Profile: {analysis.profile[:1800]}",
            f"Key Points: {str(analysis.key_points)[:1000]}",
        ])

    except DocumentAnalysis.DoesNotExist:
        analysis_text = ""

    if not analysis_text:
        return fallback_query

    prompt = f"""
You are helping build a literature review search query.

Create ONE concise academic search query for finding related published research papers.

Rules:
- Return only the search query.
- No explanation.
- 6 to 14 words.
- Focus on research topic, method, domain, and problem.
- Avoid generic words like "study", "paper", "document", "report".
- Do not include quotes.

Document title:
{paper.title}

Document intelligence:
{analysis_text}
"""

    try:
        query = generate_llm_answer(prompt)
        query = clean_text(query)
        query = query.replace('"', "").replace("'", "")

        if not query or len(query.split()) < 3:
            return fallback_query

        return query[:240]

    except Exception:
        return fallback_query


def build_why_related(result, search_query):
    concepts = result.get("concepts") or []

    if concepts:
        concept_text = ", ".join(concepts[:4])
        return (
            f"Matched the generated literature query '{search_query}' and "
            f"overlaps with research concepts such as {concept_text}."
        )

    return (
        f"Matched the generated literature query '{search_query}' through "
        "title, abstract, or indexed scholarly metadata."
    )


def save_related_results(paper, results, search_query, clear_existing=True):
    if clear_existing:
        RelatedPaper.objects.filter(paper=paper).delete()

    saved_items = []

    for item in results:
        related = RelatedPaper.objects.create(
            paper=paper,
            source=item.get("source") or "OpenAlex",
            openalex_id=item.get("openalex_id") or "",
            title=item.get("title") or "",
            authors=item.get("authors") or [],
            year=item.get("year"),
            publication_date=item.get("publication_date") or "",
            venue=item.get("venue") or "",
            doi=item.get("doi") or "",
            url=item.get("url") or "",
            pdf_url=item.get("pdf_url") or "",
            open_access=bool(item.get("open_access")),
            open_access_status=item.get("open_access_status") or "",
            work_type=item.get("type") or "",
            cited_by_count=item.get("cited_by_count") or 0,
            abstract=item.get("abstract") or "",
            concepts=item.get("concepts") or [],
            search_query=search_query,
            why_related=build_why_related(item, search_query),
        )

        saved_items.append(related)

    return saved_items


def generate_related_papers_for_document(
    paper_id,
    limit=10,
    from_year=2018,
    to_year=None,
    open_access_only=False,
):
    try:
        paper = Paper.objects.get(id=paper_id)
    except Paper.DoesNotExist:
        raise ValueError("Paper not found.")

    if paper.status != "ready":
        raise ValueError("Only ready documents can generate related literature.")

    search_query = build_related_literature_query(paper)

    scholar_results = search_openalex_works(
        query=search_query,
        limit=limit,
        from_year=from_year,
        to_year=to_year,
        open_access_only=open_access_only,
    )

    results = scholar_results.get("results") or []

    saved_items = save_related_results(
        paper=paper,
        results=results,
        search_query=search_query,
        clear_existing=True,
    )

    return {
        "paper": paper,
        "search_query": search_query,
        "count": len(saved_items),
        "items": saved_items,
    }