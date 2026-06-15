import re

from .config import (
    RAG_TOP_K,
    MAX_CONTEXT_CHARS_PER_CHUNK,
    REPORT_FIRST_CHUNKS,
    REPORT_LAST_CHUNKS,
    REPORT_MAX_TOTAL_SOURCES,
    ANALYSIS_PROFILE_MAX_CHARS,
    ANALYSIS_SUMMARY_MAX_CHARS_FOR_RAG,
)
from .embedding_service import generate_embedding
from .vector_service import search_similar_chunks
from .llm_service import generate_llm_answer
from ..models import PaperChunk, DocumentAnalysis, ChatMessage


CHAT_MEMORY_LIMIT = 8


OVERVIEW_KEYWORDS = [
    "summary",
    "summarize",
    "main theme",
    "theme",
    "main idea",
    "main goal",
    "goal",
    "goals",
    "objective",
    "objectives",
    "overview",
    "what is this report about",
    "what is this paper about",
    "what is this project about",
    "main contribution",
    "contribution",
    "purpose",
    "full report",
    "whole report",
    "overall",
    "project overview",
    "document overview",
]

PROJECT_KEYWORDS = [
    "project",
    "system",
    "application",
    "software",
    "implementation",
    "module",
    "technology",
    "architecture",
    "database",
    "testing",
    "requirement",
    "design",
]

METHODOLOGY_KEYWORDS = [
    "methodology",
    "method",
    "methods",
    "approach",
    "process",
    "procedure",
    "workflow",
    "how",
    "step by step",
]

GAP_KEYWORDS = [
    "research gap",
    "gap",
    "limitation",
    "limitations",
    "future work",
    "future direction",
    "future scope",
]

DESIGN_KEYWORDS = [
    "architecture",
    "system design",
    "design",
    "database",
    "er diagram",
    "use case",
    "module",
    "dfd",
    "data flow",
    "class diagram",
    "sequence diagram",
]

IMPLEMENTATION_KEYWORDS = [
    "implementation",
    "technology stack",
    "technologies",
    "tools",
    "frontend",
    "backend",
    "api",
    "database",
    "deployment",
]

TESTING_KEYWORDS = [
    "testing",
    "test case",
    "test cases",
    "result",
    "results",
    "evaluation",
]


FOUNDATION_SECTIONS = [
    "Abstract",
    "Executive Summary",
    "Summary",
    "Overview",
    "Introduction",
    "Background",
    "Project Overview",
    "System Overview",
    "Problem Statement",
    "Objectives",
    "Scope",
    "Conclusion",
    "Future Work",
    "Future Scope",
]

PROJECT_SECTIONS = [
    "Project Overview",
    "System Overview",
    "Problem Statement",
    "Objectives",
    "Scope",
    "Requirement Analysis",
    "Functional Requirements",
    "Non Functional Requirements",
    "System Analysis",
    "System Design",
    "System Architecture",
    "Database Design",
    "ER Diagram",
    "Use Case Diagram",
    "Module Description",
    "Module Breakdown",
    "Implementation",
    "Technology Stack",
    "Testing",
    "Results",
    "Conclusion",
    "Future Scope",
]

METHODOLOGY_SECTIONS = [
    "Methodology",
    "Methods",
    "Proposed Method",
    "Proposed System",
    "System Model",
    "Model Architecture",
    "Experimental Setup",
    "Implementation",
    "System Architecture",
    "System Design",
]

DESIGN_SECTIONS = [
    "System Design",
    "System Architecture",
    "Database Design",
    "ER Diagram",
    "Use Case Diagram",
    "Class Diagram",
    "Sequence Diagram",
    "Activity Diagram",
    "Data Flow Diagram",
    "Module Description",
    "Module Breakdown",
]

IMPLEMENTATION_SECTIONS = [
    "Implementation",
    "Technology Stack",
    "Frontend",
    "Backend",
    "API",
    "Database Design",
    "Deployment",
]

TESTING_SECTIONS = [
    "Testing",
    "Test Cases",
    "Evaluation",
    "Results",
    "Findings",
]


NOISE_PATTERNS = [
    "scanned with camscanner",
    "camscanner",
    "page intentionally left blank",
]


def contains_any(question, keywords):
    q = question.lower()
    return any(keyword in q for keyword in keywords)


def is_overview_question(question):
    return contains_any(question, OVERVIEW_KEYWORDS)


def is_project_question(question):
    return contains_any(question, PROJECT_KEYWORDS)


def is_methodology_question(question):
    return contains_any(question, METHODOLOGY_KEYWORDS)


def is_gap_question(question):
    return contains_any(question, GAP_KEYWORDS)


def is_design_question(question):
    return contains_any(question, DESIGN_KEYWORDS)


def is_implementation_question(question):
    return contains_any(question, IMPLEMENTATION_KEYWORDS)


def is_testing_question(question):
    return contains_any(question, TESTING_KEYWORDS)


def truncate_text(text, max_chars):
    if not text:
        return ""

    text = text.strip()

    if len(text) <= max_chars:
        return text

    return text[:max_chars].rsplit(" ", 1)[0].strip()


def clean_source_content(text):
    if not text:
        return ""

    lines = []

    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()

        if not line:
            continue

        lower_line = line.lower()

        if any(pattern in lower_line for pattern in NOISE_PATTERNS):
            continue

        lines.append(line)

    return "\n".join(lines).strip()


def is_low_quality_source(content):
    if not content:
        return True

    cleaned = clean_source_content(content)

    if len(cleaned) < 80:
        return True

    words = re.findall(r"[A-Za-z]{3,}", cleaned)

    if len(words) < 12:
        return True

    return False


def get_recent_chat_memory(paper_id, current_question=None):
    messages = list(
        ChatMessage.objects.filter(paper_id=paper_id)
        .order_by("-created_at")[:CHAT_MEMORY_LIMIT]
    )

    messages.reverse()

    memory_parts = []

    for message in messages:
        text = (message.message or "").strip()

        if not text:
            continue

        if (
            current_question
            and message.role == "user"
            and text.strip().lower() == current_question.strip().lower()
        ):
            continue

        role = "User" if message.role == "user" else "Assistant"
        memory_parts.append(f"{role}: {truncate_text(text, 700)}")

    if not memory_parts:
        return ""

    return "\n".join(memory_parts)


def get_relevant_analysis_sections(question, section_summaries):
    preferred_sections = []

    if is_overview_question(question):
        preferred_sections.extend([
            "Abstract",
            "Executive Summary",
            "Summary",
            "Overview",
            "Introduction",
            "Project Overview",
            "Problem Statement",
            "Objectives",
            "Conclusion",
            "Future Scope",
            "Future Work",
        ])

    if is_methodology_question(question):
        preferred_sections.extend(METHODOLOGY_SECTIONS)

    if is_design_question(question):
        preferred_sections.extend(DESIGN_SECTIONS)

    if is_implementation_question(question):
        preferred_sections.extend(IMPLEMENTATION_SECTIONS)

    if is_testing_question(question):
        preferred_sections.extend(TESTING_SECTIONS)

    if is_gap_question(question):
        preferred_sections.extend([
            "Problem Statement",
            "Introduction",
            "Limitations",
            "Future Scope",
            "Future Work",
            "Discussion",
            "Conclusion",
        ])

    selected = []
    used = set()

    for section in preferred_sections:
        if section in section_summaries and section not in used:
            selected.append(section)
            used.add(section)

        if len(selected) >= 5:
            return selected

    for section in section_summaries.keys():
        if section not in used:
            selected.append(section)
            used.add(section)

        if len(selected) >= 5:
            break

    return selected


def get_document_analysis_context(paper_id, question):
    try:
        analysis = DocumentAnalysis.objects.get(
            paper_id=paper_id,
            status="ready"
        )
    except DocumentAnalysis.DoesNotExist:
        return ""

    parts = []

    if analysis.document_type:
        parts.append(f"Document Type: {analysis.document_type}")

    if analysis.profile:
        parts.append(
            f"""
Whole Document Intelligence Profile:
{truncate_text(analysis.profile, ANALYSIS_PROFILE_MAX_CHARS)}
"""
        )

    section_summaries = analysis.section_summaries or {}
    relevant_sections = get_relevant_analysis_sections(question, section_summaries)

    if relevant_sections:
        section_parts = []

        for section in relevant_sections:
            summary = section_summaries.get(section)

            if not summary:
                continue

            section_parts.append(
                f"""
Section: {section}
Summary:
{truncate_text(summary, 900)}
"""
            )

        combined = "\n\n".join(section_parts)

        parts.append(
            f"""
Relevant Section Summaries:
{truncate_text(combined, ANALYSIS_SUMMARY_MAX_CHARS_FOR_RAG)}
"""
        )

    return "\n\n".join(parts).strip()


def get_default_source_limit(question):
    if is_overview_question(question):
        return 6

    if is_methodology_question(question):
        return 5

    if is_design_question(question):
        return 5

    if is_implementation_question(question):
        return 5

    if is_testing_question(question):
        return 4

    if is_gap_question(question):
        return 4

    return 3


def get_prompt_source_limit(question):
    if is_overview_question(question):
        return min(8, REPORT_MAX_TOTAL_SOURCES)

    if (
        is_methodology_question(question)
        or is_design_question(question)
        or is_implementation_question(question)
    ):
        return min(7, REPORT_MAX_TOTAL_SOURCES)

    return min(5, REPORT_MAX_TOTAL_SOURCES)


def get_distance_score(distance):
    """
    Chroma distance can vary depending on embedding metric.
    Lower distance usually means better match.
    This converts it into an approximate quality label.
    """

    if distance is None:
        return 0.60, "Context source"

    try:
        distance = float(distance)
    except Exception:
        return 0.60, "Context source"

    if distance <= 0.35:
        return 0.95, "Very strong match"

    if distance <= 0.60:
        return 0.85, "Strong match"

    if distance <= 0.90:
        return 0.70, "Moderate match"

    if distance <= 1.20:
        return 0.55, "Weak match"

    return 0.40, "Low confidence"


def section_boost(question, section_title):
    section = (section_title or "").lower()

    boost = 0.0

    if is_overview_question(question):
        if section in [
            "abstract",
            "introduction",
            "overview",
            "project overview",
            "executive summary",
            "summary",
            "conclusion",
        ]:
            boost += 0.12

    if is_methodology_question(question):
        if "method" in section or "approach" in section or "proposed" in section:
            boost += 0.15

    if is_design_question(question):
        if "design" in section or "architecture" in section or "diagram" in section:
            boost += 0.15

    if is_implementation_question(question):
        if (
            "implementation" in section
            or "technology" in section
            or "frontend" in section
            or "backend" in section
            or "api" in section
        ):
            boost += 0.15

    if is_testing_question(question):
        if "testing" in section or "result" in section or "evaluation" in section:
            boost += 0.15

    if is_gap_question(question):
        if "limitation" in section or "future" in section or "problem" in section:
            boost += 0.15

    return boost


def calculate_source_quality(source, question):
    content = source.get("content") or ""
    distance = source.get("distance")
    section_title = source.get("section_title") or "Unknown"

    base_score, base_label = get_distance_score(distance)

    content_length_bonus = 0.0
    cleaned = clean_source_content(content)

    if len(cleaned) > 400:
        content_length_bonus += 0.05

    if len(cleaned) > 800:
        content_length_bonus += 0.05

    quality_score = base_score + content_length_bonus + section_boost(question, section_title)
    quality_score = max(0.0, min(1.0, quality_score))

    if quality_score >= 0.90:
        label = "Very strong match"
    elif quality_score >= 0.75:
        label = "Strong match"
    elif quality_score >= 0.60:
        label = "Moderate match"
    elif quality_score >= 0.45:
        label = "Weak match"
    else:
        label = "Low confidence"

    source["relevance_score"] = round(quality_score, 2)
    source["relevance_label"] = label
    source["base_relevance_label"] = base_label
    source["preview"] = truncate_text(cleaned, 180)

    return source


def rank_and_filter_sources(sources, question):
    clean_sources = []

    seen_content = set()

    for source in sources:
        content = source.get("content") or ""
        cleaned = clean_source_content(content)

        if is_low_quality_source(cleaned):
            continue

        normalized_content = re.sub(r"\s+", " ", cleaned.lower())[:300]

        if normalized_content in seen_content:
            continue

        seen_content.add(normalized_content)

        source["content"] = truncate_text(cleaned, MAX_CONTEXT_CHARS_PER_CHUNK)
        source = calculate_source_quality(source, question)

        clean_sources.append(source)

    clean_sources.sort(
        key=lambda item: (
            item.get("relevance_score", 0),
            -1 * (item.get("distance") or 0 if isinstance(item.get("distance"), (int, float)) else 0),
        ),
        reverse=True,
    )

    limit = get_prompt_source_limit(question)

    return clean_sources[:limit]


def assign_source_ids(sources):
    for index, source in enumerate(sources, start=1):
        source["source_id"] = f"S{index}"

    return sources


def build_context_from_sources(sources):
    assign_source_ids(sources)

    context_parts = []

    for source in sources:
        source_id = source.get("source_id") or "S?"
        page_number = source.get("page_number") or "Unknown"
        start_line = source.get("start_line") or "Unknown"
        end_line = source.get("end_line") or "Unknown"
        section_title = source.get("section_title") or "Unknown"
        relevance_label = source.get("relevance_label") or "Context source"
        relevance_score = source.get("relevance_score")
        content = source.get("content") or ""

        if not content.strip():
            continue

        context_parts.append(
            f"""
Source ID: [{source_id}]
Page Number: {page_number}
Line Range: {start_line}-{end_line}
Section: {section_title}
Source Relevance: {relevance_label}
Relevance Score: {relevance_score}

Content:
{content}
"""
        )

    return "\n\n".join(context_parts)


def build_rag_prompt(
    analysis_context,
    retrieved_context,
    chat_memory,
    question,
    has_sources=True,
):
    no_info_rule = """
- If no document context is provided, say:
  "The document does not provide enough information."
"""

    source_rule = """
- Document context IS provided.
- Do NOT answer "The document does not provide enough information" unless all provided context is empty or irrelevant.
- If the context is partial, still give the best possible answer based on the available document intelligence, conversation memory, and retrieved evidence.
- When information is incomplete, clearly say what is directly supported and what is missing.
"""

    return f"""
You are ScholarMind, a deep academic document analysis assistant.

You can analyze:
- Research papers
- Thesis reports
- Project reports
- Technical reports
- Lab reports
- Internship reports
- Documentation PDFs
- General academic PDFs

Answer the user's question using ONLY:
1. The uploaded document context
2. The precomputed document intelligence
3. The same-paper conversation memory

Core rules:
- Use only the provided document context.
- Do not use outside knowledge.
- Do not make up information.
- Give a complete answer.
- Avoid vague statements.
- Do not stop in the middle of a section.
- Do not continue after the answer is complete.
{source_rule if has_sources else no_info_rule}

Conversation memory rules:
- Use conversation memory only to understand follow-up questions.
- Do not let old conversation override the uploaded document evidence.
- If the user asks "make it shorter", "explain that", "compare with previous answer", use recent same-paper conversation memory.

Citation rules:
- Retrieved evidence sources have IDs like [S1], [S2], [S3].
- For document-specific factual claims, cite the supporting source using [S1] style.
- Every major bullet point should include at least one citation when a retrieved source supports it.
- Do not cite a source unless it directly supports the sentence.
- Do not cite every sentence unnecessarily.
- Prefer strong and very strong sources over weak sources.
- If no retrieved source supports a claim but the document intelligence profile supports it, write: "Based on the document intelligence profile..."
- Never invent source IDs.
- Do not cite sources that are not provided.

Source quality rules:
- Use "Very strong match" and "Strong match" sources first.
- Avoid relying on weak sources unless there is no stronger evidence.
- If source support is weak or incomplete, clearly say the evidence is limited.

Quality rules:
- First understand the user's question type.
- Use the Document Intelligence Profile for whole-document understanding.
- Use retrieved source chunks as evidence.
- Separate "directly stated" information from "inferred from context" when needed.
- If a required detail is missing, explicitly say what is missing.
- Avoid generic explanations that could apply to any document.
- Every answer should be specific to this uploaded document.

Formatting rules:
- Use clean Markdown.
- Use clear headings.
- Use bullet points where helpful.
- Keep the answer academic but easy to understand.
- End broad answers with a short "Source Coverage" note.
- In Source Coverage, mention only the source IDs actually used in the answer.

Precomputed Document Intelligence:
{analysis_context if analysis_context else "No precomputed document intelligence available."}

Recent Same-Paper Conversation Memory:
{chat_memory if chat_memory else "No previous conversation memory available."}

Retrieved Source Evidence:
{retrieved_context if retrieved_context else "No retrieved source evidence available."}

User Question:
{question}

Final Answer:
"""


def source_from_chunk(chunk, distance=None):
    content = clean_source_content((chunk.content or "")[:MAX_CONTEXT_CHARS_PER_CHUNK])

    return {
        "content": content,
        "paper_id": chunk.paper_id,
        "chunk_index": chunk.chunk_index,
        "page_number": chunk.page_number,
        "start_line": chunk.start_line,
        "end_line": chunk.end_line,
        "section_title": chunk.section_title or "Unknown",
        "distance": distance,
    }


def get_chunks_by_sections(paper_id, sections, limit=5):
    return list(
        PaperChunk.objects.filter(
            paper_id=paper_id,
            section_title__in=sections,
        )
        .exclude(content__isnull=True)
        .order_by("page_number", "chunk_index")[:limit]
    )


def get_first_chunks(paper_id, limit=REPORT_FIRST_CHUNKS):
    return list(
        PaperChunk.objects.filter(paper_id=paper_id)
        .exclude(content__isnull=True)
        .order_by("chunk_index")[:limit]
    )


def get_last_chunks(paper_id, limit=REPORT_LAST_CHUNKS):
    chunks = list(
        PaperChunk.objects.filter(paper_id=paper_id)
        .exclude(content__isnull=True)
        .order_by("-chunk_index")[:limit]
    )

    return list(reversed(chunks))


def get_middle_chunks(paper_id, limit=4):
    total_chunks = PaperChunk.objects.filter(paper_id=paper_id).count()

    if total_chunks <= 0:
        return []

    if total_chunks >= 4:
        positions = [
            total_chunks // 4,
            total_chunks // 2,
            (total_chunks * 3) // 4,
        ]
    else:
        positions = [total_chunks // 2]

    chunks = []

    for pos in positions:
        chunk = (
            PaperChunk.objects.filter(paper_id=paper_id)
            .exclude(content__isnull=True)
            .order_by("chunk_index")
            .filter(chunk_index__gte=pos)
            .first()
        )

        if chunk:
            chunks.append(chunk)

        if len(chunks) >= limit:
            break

    return chunks


def add_source_if_new(sources, used_chunk_indexes, source):
    chunk_index = source.get("chunk_index")
    content = source.get("content") or ""

    if chunk_index is None:
        return

    if not content.strip():
        return

    if chunk_index in used_chunk_indexes:
        return

    if len(sources) >= REPORT_MAX_TOTAL_SOURCES:
        return

    sources.append(source)
    used_chunk_indexes.add(chunk_index)


def add_chunks_as_sources(chunks, sources, used_chunk_indexes):
    for chunk in chunks:
        add_source_if_new(
            sources,
            used_chunk_indexes,
            source_from_chunk(chunk),
        )


def add_vector_search_sources(paper_id, question, sources, used_chunk_indexes, top_k):
    query_embedding = generate_embedding(question)

    results = search_similar_chunks(
        query_embedding=query_embedding,
        paper_id=paper_id,
        top_k=top_k,
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for doc, meta, distance in zip(documents, metadatas, distances):
        meta = meta or {}

        source = {
            "content": clean_source_content((doc or "")[:MAX_CONTEXT_CHARS_PER_CHUNK]),
            "paper_id": meta.get("paper_id"),
            "chunk_index": meta.get("chunk_index"),
            "page_number": meta.get("page_number"),
            "start_line": meta.get("start_line"),
            "end_line": meta.get("end_line"),
            "section_title": meta.get("section_title") or "Unknown",
            "distance": distance,
        }

        add_source_if_new(
            sources,
            used_chunk_indexes,
            source,
        )


def extract_cited_source_ids(answer):
    if not answer:
        return []

    matches = re.findall(r"\[S(\d+)\]", answer)

    ordered_ids = []
    seen = set()

    for match in matches:
        source_id = f"S{match}"

        if source_id not in seen:
            ordered_ids.append(source_id)
            seen.add(source_id)

    return ordered_ids


def finalize_sources_for_answer(answer, sources, question):
    if not sources:
        return []

    cited_ids = extract_cited_source_ids(answer)

    if cited_ids:
        cited_sources = []

        for source_id in cited_ids:
            for source in sources:
                if source.get("source_id") == source_id:
                    source["used_in_answer"] = True
                    cited_sources.append(source)
                    break

        if cited_sources:
            return cited_sources

    fallback_limit = get_default_source_limit(question)

    fallback_sources = sources[:fallback_limit]

    for source in fallback_sources:
        source["used_in_answer"] = False
        source["fallback_reason"] = "The model did not cite sources explicitly, so ScholarMind returned the strongest retrieved sources."

    return fallback_sources


def build_rag_payload(paper_id, question, top_k=None):
    if top_k is None:
        top_k = RAG_TOP_K

    sources = []
    used_chunk_indexes = set()

    overview_question = is_overview_question(question)
    project_question = is_project_question(question)
    methodology_question = is_methodology_question(question)
    gap_question = is_gap_question(question)
    design_question = is_design_question(question)
    implementation_question = is_implementation_question(question)
    testing_question = is_testing_question(question)

    if overview_question:
        add_chunks_as_sources(
            get_first_chunks(paper_id, limit=REPORT_FIRST_CHUNKS),
            sources,
            used_chunk_indexes,
        )

        add_chunks_as_sources(
            get_chunks_by_sections(
                paper_id,
                FOUNDATION_SECTIONS,
                limit=5,
            ),
            sources,
            used_chunk_indexes,
        )

        add_chunks_as_sources(
            get_middle_chunks(paper_id, limit=3),
            sources,
            used_chunk_indexes,
        )

        add_chunks_as_sources(
            get_last_chunks(paper_id, limit=REPORT_LAST_CHUNKS),
            sources,
            used_chunk_indexes,
        )

    if project_question:
        add_chunks_as_sources(
            get_chunks_by_sections(
                paper_id,
                PROJECT_SECTIONS,
                limit=7,
            ),
            sources,
            used_chunk_indexes,
        )

    if methodology_question:
        add_chunks_as_sources(
            get_chunks_by_sections(
                paper_id,
                METHODOLOGY_SECTIONS,
                limit=6,
            ),
            sources,
            used_chunk_indexes,
        )

    if design_question:
        add_chunks_as_sources(
            get_chunks_by_sections(
                paper_id,
                DESIGN_SECTIONS,
                limit=6,
            ),
            sources,
            used_chunk_indexes,
        )

    if implementation_question:
        add_chunks_as_sources(
            get_chunks_by_sections(
                paper_id,
                IMPLEMENTATION_SECTIONS,
                limit=6,
            ),
            sources,
            used_chunk_indexes,
        )

    if testing_question:
        add_chunks_as_sources(
            get_chunks_by_sections(
                paper_id,
                TESTING_SECTIONS,
                limit=5,
            ),
            sources,
            used_chunk_indexes,
        )

    if gap_question:
        add_chunks_as_sources(
            get_chunks_by_sections(
                paper_id,
                [
                    "Introduction",
                    "Problem Statement",
                    "Limitations",
                    "Future Work",
                    "Future Scope",
                    "Discussion",
                    "Conclusion",
                ],
                limit=6,
            ),
            sources,
            used_chunk_indexes,
        )

    add_vector_search_sources(
        paper_id=paper_id,
        question=question,
        sources=sources,
        used_chunk_indexes=used_chunk_indexes,
        top_k=top_k,
    )

    if not sources:
        add_chunks_as_sources(
            get_first_chunks(paper_id, limit=REPORT_FIRST_CHUNKS),
            sources,
            used_chunk_indexes,
        )

        add_chunks_as_sources(
            get_middle_chunks(paper_id, limit=3),
            sources,
            used_chunk_indexes,
        )

        add_chunks_as_sources(
            get_last_chunks(paper_id, limit=REPORT_LAST_CHUNKS),
            sources,
            used_chunk_indexes,
        )

    sources = rank_and_filter_sources(sources, question)

    retrieved_context = build_context_from_sources(sources)
    analysis_context = get_document_analysis_context(paper_id, question)
    chat_memory = get_recent_chat_memory(paper_id, current_question=question)

    has_context = bool(
        retrieved_context.strip()
        or analysis_context.strip()
        or chat_memory.strip()
    )

    if not has_context:
        return {
            "prompt": build_rag_prompt(
                analysis_context="",
                retrieved_context="No relevant context found.",
                chat_memory="",
                question=question,
                has_sources=False,
            ),
            "sources": [],
        }

    prompt = build_rag_prompt(
        analysis_context=analysis_context,
        retrieved_context=retrieved_context,
        chat_memory=chat_memory,
        question=question,
        has_sources=True,
    )

    return {
        "prompt": prompt,
        "sources": sources,
    }


def ask_question_from_paper(paper_id, question, top_k=None):
    rag_payload = build_rag_payload(
        paper_id=paper_id,
        question=question,
        top_k=top_k,
    )

    answer = generate_llm_answer(rag_payload["prompt"])

    used_sources = finalize_sources_for_answer(
        answer=answer,
        sources=rag_payload["sources"],
        question=question,
    )

    return {
        "answer": answer,
        "sources": used_sources,
    }