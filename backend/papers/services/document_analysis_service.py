from collections import defaultdict

from ..models import PaperChunk, DocumentAnalysis
from .llm_service import generate_llm_answer
from .config import (
    ANALYSIS_MAX_SECTIONS,
    ANALYSIS_MAX_CHUNKS_PER_SECTION,
    ANALYSIS_MAX_CHARS_PER_SECTION,
)


SECTION_PRIORITY = [
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
    "Literature Review",
    "Related Work",
    "Requirement Analysis",
    "System Analysis",
    "Methodology",
    "Methods",
    "Proposed Method",
    "Proposed System",
    "System Design",
    "System Architecture",
    "Database Design",
    "ER Diagram",
    "Use Case Diagram",
    "Module Description",
    "Implementation",
    "Technology Stack",
    "Testing",
    "Evaluation",
    "Results",
    "Findings",
    "Discussion",
    "Limitations",
    "Future Work",
    "Future Scope",
    "Conclusion",
]


PROJECT_KEYWORDS = [
    "project",
    "system design",
    "implementation",
    "technology stack",
    "frontend",
    "backend",
    "database",
    "module",
    "testing",
    "requirement analysis",
    "use case",
    "er diagram",
]

RESEARCH_KEYWORDS = [
    "abstract",
    "methodology",
    "related work",
    "literature review",
    "experiment",
    "evaluation",
    "dataset",
    "result",
    "research gap",
]

THESIS_KEYWORDS = [
    "chapter",
    "supervisor",
    "department",
    "thesis",
    "dissertation",
    "submitted by",
    "submitted to",
]


def truncate_text(text, max_chars):
    if not text:
        return ""

    text = text.strip()

    if len(text) <= max_chars:
        return text

    return text[:max_chars].rsplit(" ", 1)[0].strip()


def count_keyword_score(text, keywords):
    lower_text = text.lower()
    return sum(lower_text.count(keyword) for keyword in keywords)


def infer_document_type_from_chunks(chunks):
    sample_parts = []

    for chunk in chunks[:80]:
        sample_parts.append(chunk.section_title or "")
        sample_parts.append((chunk.content or "")[:800])

    sample = "\n".join(sample_parts).lower()

    project_score = count_keyword_score(sample, PROJECT_KEYWORDS)
    research_score = count_keyword_score(sample, RESEARCH_KEYWORDS)
    thesis_score = count_keyword_score(sample, THESIS_KEYWORDS)

    if thesis_score >= 3:
        return "Thesis or Academic Report"

    if project_score >= research_score and project_score >= 4:
        return "Project Report"

    if research_score >= 4:
        return "Research Paper"

    if "internship" in sample:
        return "Internship Report"

    if "lab report" in sample or "experiment" in sample:
        return "Lab Report"

    return "General Academic Document"


def select_representative_chunks(chunks, max_chunks):
    if len(chunks) <= max_chunks:
        return chunks

    selected = []
    positions = [
        0,
        len(chunks) // 3,
        (len(chunks) * 2) // 3,
        len(chunks) - 1,
    ]

    used_indexes = set()

    for pos in positions:
        chunk = chunks[pos]

        if chunk.chunk_index not in used_indexes:
            selected.append(chunk)
            used_indexes.add(chunk.chunk_index)

        if len(selected) >= max_chunks:
            break

    return selected


def build_section_text(section_title, chunks):
    selected_chunks = select_representative_chunks(
        chunks,
        max_chunks=ANALYSIS_MAX_CHUNKS_PER_SECTION,
    )

    parts = []

    for chunk in selected_chunks:
        page = chunk.page_number or "Unknown"
        lines = ""

        if chunk.start_line and chunk.end_line:
            lines = f", Lines {chunk.start_line}-{chunk.end_line}"

        parts.append(
            f"""
Page {page}{lines}
Chunk {chunk.chunk_index}
{chunk.content}
"""
        )

    combined = "\n\n".join(parts)

    return truncate_text(combined, ANALYSIS_MAX_CHARS_PER_SECTION)


def summarize_section(section_title, section_text, document_type):
    prompt = f"""
You are ScholarMind, an academic document analysis assistant.

Document type:
{document_type}

You are analyzing this section:
{section_title}

Use ONLY the provided section text.

Your task:
Create a clear section summary that helps future Q&A.

Rules:
- Do not use outside knowledge.
- Do not invent information.
- Keep the summary specific and evidence-based.
- Mention important facts, methods, tools, results, or limitations if present.
- If the section text is weak or incomplete, say what is unclear.

Section Text:
{section_text}

Return format:

## Section Purpose
...

## Important Details
- ...

## Evidence Available
- ...

## Missing or Unclear
- ...
"""

    return generate_llm_answer(prompt)


def group_chunks_by_section(chunks):
    grouped = defaultdict(list)

    for chunk in chunks:
        section = chunk.section_title or "Unknown"

        if section == "Unknown":
            section = "Document Body"

        grouped[section].append(chunk)

    return grouped


def choose_sections_for_analysis(grouped_sections):
    selected_sections = []

    for section in SECTION_PRIORITY:
        if section in grouped_sections and section not in selected_sections:
            selected_sections.append(section)

        if len(selected_sections) >= ANALYSIS_MAX_SECTIONS:
            return selected_sections

    for section in grouped_sections.keys():
        if section not in selected_sections:
            selected_sections.append(section)

        if len(selected_sections) >= ANALYSIS_MAX_SECTIONS:
            break

    return selected_sections


def generate_profile(document_type, section_summaries):
    summaries_text_parts = []

    for section, summary in section_summaries.items():
        summaries_text_parts.append(
            f"""
====================
SECTION: {section}
====================
{summary}
"""
        )

    summaries_text = "\n\n".join(summaries_text_parts)

    prompt = f"""
You are ScholarMind, an academic document intelligence engine.

Document type:
{document_type}

You are given section summaries generated from the uploaded document.
Use ONLY these section summaries.

Create a complete whole-document intelligence profile.

Rules:
- Do not use outside knowledge.
- Do not invent missing details.
- Separate directly supported information from inferred information.
- If something is not available, write "Not clearly available in the provided document context."
- Be specific and non-vague.
- The final profile will be used for future Q&A, so make it structured and useful.

Section Summaries:
{summaries_text}

Return this exact structure:

# Document Intelligence Profile

## Document Type
...

## Main Theme
...

## Problem / Need Being Addressed
...

## Objectives
- ...

## Methodology / Approach
...

## System Design / Architecture
...

## Implementation / Technology
...

## Testing / Evaluation / Results
...

## Key Findings or Outputs
- ...

## Limitations
- ...

## Future Scope / Future Work
- ...

## Important Terms
- ...

## Source Coverage
Mention which sections were available and which important sections were missing.

## Missing or Unclear Areas
- ...
"""

    return generate_llm_answer(prompt)


def build_key_points(profile, section_summaries):
    return {
        "profile_available": bool(profile.strip()),
        "sections_analyzed": list(section_summaries.keys()),
        "section_count": len(section_summaries),
    }


def analyze_document(paper, progress_callback=None):
    analysis, _ = DocumentAnalysis.objects.update_or_create(
        paper=paper,
        defaults={
            "status": "processing",
            "document_type": "Analyzing",
            "profile": "",
            "section_summaries": {},
            "key_points": {},
            "source_coverage": {},
            "error_message": "",
        }
    )

    try:
        chunks = list(
            PaperChunk.objects.filter(paper=paper)
            .exclude(content__isnull=True)
            .order_by("chunk_index")
        )

        if not chunks:
            raise ValueError("No chunks found for document analysis.")

        document_type = infer_document_type_from_chunks(chunks)

        if progress_callback:
            progress_callback(
                stage="Building document intelligence",
                percent=88,
                details=f"Detected document type: {document_type}."
            )

        grouped_sections = group_chunks_by_section(chunks)
        selected_sections = choose_sections_for_analysis(grouped_sections)

        section_summaries = {}

        total_sections = len(selected_sections)

        for index, section_title in enumerate(selected_sections, start=1):
            if progress_callback:
                percent = 88 + int((index / max(total_sections, 1)) * 7)

                progress_callback(
                    stage="Summarizing sections",
                    percent=percent,
                    details=f"Summarizing section {index} of {total_sections}: {section_title}."
                )

            section_text = build_section_text(
                section_title=section_title,
                chunks=grouped_sections[section_title],
            )

            if not section_text.strip():
                continue

            summary = summarize_section(
                section_title=section_title,
                section_text=section_text,
                document_type=document_type,
            )

            section_summaries[section_title] = summary

        if progress_callback:
            progress_callback(
                stage="Creating document profile",
                percent=96,
                details="Combining section summaries into a whole-document profile."
            )

        profile = generate_profile(
            document_type=document_type,
            section_summaries=section_summaries,
        )

        key_points = build_key_points(profile, section_summaries)

        source_coverage = {
            "document_type": document_type,
            "sections_analyzed": list(section_summaries.keys()),
            "total_chunks": len(chunks),
            "total_sections_detected": len(grouped_sections),
        }

        analysis.document_type = document_type
        analysis.status = "ready"
        analysis.profile = profile
        analysis.section_summaries = section_summaries
        analysis.key_points = key_points
        analysis.source_coverage = source_coverage
        analysis.error_message = ""
        analysis.save()

        return analysis

    except Exception as e:
        analysis.status = "failed"
        analysis.error_message = str(e)
        analysis.save()
        raise