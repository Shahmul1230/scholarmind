import re


SECTION_KEYWORDS = {
    # General academic sections
    "abstract": "Abstract",
    "executive summary": "Executive Summary",
    "summary": "Summary",
    "overview": "Overview",
    "introduction": "Introduction",
    "background": "Background",
    "literature review": "Literature Review",
    "related work": "Related Work",
    "problem statement": "Problem Statement",
    "motivation": "Motivation",
    "objectives": "Objectives",
    "objective": "Objectives",
    "aim": "Objectives",
    "aims": "Objectives",
    "scope": "Scope",
    "project scope": "Scope",

    # Research paper sections
    "method": "Methodology",
    "methods": "Methodology",
    "methodology": "Methodology",
    "materials and methods": "Methodology",
    "research methodology": "Methodology",
    "proposed method": "Proposed Method",
    "proposed approach": "Proposed Method",
    "proposed system": "Proposed System",
    "system model": "System Model",
    "model architecture": "Model Architecture",
    "experiment": "Experiments",
    "experiments": "Experiments",
    "experimental setup": "Experimental Setup",
    "evaluation": "Evaluation",
    "results": "Results",
    "result": "Results",
    "findings": "Findings",
    "discussion": "Discussion",
    "analysis": "Analysis",
    "limitation": "Limitations",
    "limitations": "Limitations",
    "future work": "Future Work",
    "future scope": "Future Scope",
    "conclusion": "Conclusion",
    "references": "References",

    # Project report sections
    "project overview": "Project Overview",
    "system overview": "System Overview",
    "requirement analysis": "Requirement Analysis",
    "requirements analysis": "Requirement Analysis",
    "functional requirements": "Functional Requirements",
    "non functional requirements": "Non Functional Requirements",
    "non-functional requirements": "Non Functional Requirements",
    "software requirements": "Software Requirements",
    "hardware requirements": "Hardware Requirements",
    "feasibility study": "Feasibility Study",
    "system analysis": "System Analysis",
    "system design": "System Design",
    "design": "System Design",
    "architecture": "System Architecture",
    "system architecture": "System Architecture",
    "application architecture": "System Architecture",
    "database design": "Database Design",
    "database schema": "Database Design",
    "er diagram": "ER Diagram",
    "erd": "ER Diagram",
    "use case diagram": "Use Case Diagram",
    "use case": "Use Case Diagram",
    "class diagram": "Class Diagram",
    "sequence diagram": "Sequence Diagram",
    "activity diagram": "Activity Diagram",
    "data flow diagram": "Data Flow Diagram",
    "dfd": "Data Flow Diagram",
    "module description": "Module Description",
    "modules": "Module Description",
    "module breakdown": "Module Breakdown",
    "implementation": "Implementation",
    "implementation details": "Implementation",
    "technology stack": "Technology Stack",
    "technologies used": "Technology Stack",
    "tools and technologies": "Technology Stack",
    "development tools": "Technology Stack",
    "frontend": "Frontend",
    "backend": "Backend",
    "api": "API",
    "testing": "Testing",
    "test case": "Testing",
    "test cases": "Testing",
    "deployment": "Deployment",
    "user manual": "User Manual",
    "screenshots": "Screenshots",
    "appendix": "Appendix",
}


def clean_text_line(line):
    line = line.strip()
    line = re.sub(r"\s+", " ", line)
    return line


def normalize_heading(line):
    line = line.lower().strip()

    # Remove common numbering patterns:
    # 1. Introduction
    # 1.1 Background
    # Chapter 1 Introduction
    # I. Introduction
    line = re.sub(r"^chapter\s+\d+\s*[:.-]?\s*", "", line)
    line = re.sub(r"^\d+(\.\d+)*\s*[:.-]?\s*", "", line)
    line = re.sub(r"^[ivxlcdm]+\s*[:.-]\s*", "", line)

    # Remove symbols but keep useful words
    line = re.sub(r"[^a-z0-9\s\-]", " ", line)
    line = re.sub(r"\s+", " ", line)

    return line.strip()


def looks_like_heading(line):
    cleaned = line.strip()

    if not cleaned:
        return False

    # Very long text is probably not heading
    if len(cleaned) > 90:
        return False

    normalized = normalize_heading(cleaned)

    if not normalized:
        return False

    # Exact known heading
    if normalized in SECTION_KEYWORDS:
        return True

    # Starts with known heading
    for keyword in SECTION_KEYWORDS.keys():
        if normalized.startswith(keyword) and len(normalized) <= 90:
            return True

    # Common report heading style: mostly title case / uppercase and short
    words = cleaned.split()
    if 1 <= len(words) <= 8:
        uppercase_count = sum(1 for ch in cleaned if ch.isupper())
        alpha_count = sum(1 for ch in cleaned if ch.isalpha())

        if alpha_count > 0 and uppercase_count / alpha_count > 0.55:
            return True

    return False


def detect_section_title(line, current_section):
    normalized = normalize_heading(line)

    if not normalized:
        return current_section

    if normalized in SECTION_KEYWORDS:
        return SECTION_KEYWORDS[normalized]

    for keyword, title in SECTION_KEYWORDS.items():
        if normalized.startswith(keyword) and len(normalized) <= 90:
            return title

    return current_section


def create_chunk(chunk_index, page_number, items, section_title):
    lines = [item["text"] for item in items]
    content = "\n".join(lines).strip()

    return {
        "chunk_index": chunk_index,
        "content": content,
        "page_number": page_number,
        "start_line": items[0]["line_number"],
        "end_line": items[-1]["line_number"],
        "section_title": section_title or "Unknown",
    }


def chunk_pages(pages, chunk_size=1400, overlap_lines=3):
    chunks = []
    chunk_index = 0
    current_section = "Unknown"

    for page in pages:
        page_number = page.get("page_number")
        lines = page.get("lines", [])

        current_items = []
        current_chars = 0
        chunk_section = current_section

        for line_number, raw_line in enumerate(lines, start=1):
            line = clean_text_line(raw_line)

            if not line:
                continue

            if looks_like_heading(line):
                current_section = detect_section_title(line, current_section)

            if not current_items:
                chunk_section = current_section

            line_chars = len(line) + 1

            if current_items and current_chars + line_chars > chunk_size:
                chunks.append(
                    create_chunk(
                        chunk_index=chunk_index,
                        page_number=page_number,
                        items=current_items,
                        section_title=chunk_section,
                    )
                )

                chunk_index += 1

                if overlap_lines > 0:
                    current_items = current_items[-overlap_lines:]
                    current_chars = sum(
                        len(item["text"]) + 1 for item in current_items
                    )
                else:
                    current_items = []
                    current_chars = 0

                chunk_section = current_section

            current_items.append({
                "line_number": line_number,
                "text": line,
            })
            current_chars += line_chars

        if current_items:
            chunks.append(
                create_chunk(
                    chunk_index=chunk_index,
                    page_number=page_number,
                    items=current_items,
                    section_title=chunk_section,
                )
            )
            chunk_index += 1

    return chunks


def chunk_text(data, chunk_size=1400, overlap=250):
    """
    Supports:
    1. New page-wise format: list of pages
    2. Old plain text format: string
    """

    if not data:
        return []

    if isinstance(data, list):
        return chunk_pages(
            pages=data,
            chunk_size=chunk_size,
            overlap_lines=3
        )

    if isinstance(data, str):
        chunks = []
        start = 0
        chunk_index = 0
        text_length = len(data)

        while start < text_length:
            end = start + chunk_size
            chunk_content = data[start:end].strip()

            if chunk_content:
                chunks.append({
                    "chunk_index": chunk_index,
                    "content": chunk_content,
                    "page_number": None,
                    "start_line": None,
                    "end_line": None,
                    "section_title": "Unknown",
                })

            chunk_index += 1
            start += chunk_size - overlap

        return chunks

    return []