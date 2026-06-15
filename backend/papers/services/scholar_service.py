import re
import requests

from .config import (
    OPENALEX_BASE_URL,
    OPENALEX_MAILTO,
    SCHOLAR_SEARCH_DEFAULT_LIMIT,
    SCHOLAR_SEARCH_MAX_LIMIT,
    SCHOLAR_SEARCH_TIMEOUT,
)


def clamp_limit(limit):
    try:
        limit = int(limit)
    except Exception:
        limit = SCHOLAR_SEARCH_DEFAULT_LIMIT

    if limit < 1:
        return 1

    if limit > SCHOLAR_SEARCH_MAX_LIMIT:
        return SCHOLAR_SEARCH_MAX_LIMIT

    return limit


def reconstruct_abstract(abstract_inverted_index):
    """
    OpenAlex returns abstract as inverted index:
    {
      "word": [position1, position2]
    }

    This function reconstructs it into readable text.
    """

    if not abstract_inverted_index:
        return ""

    position_to_word = {}

    for word, positions in abstract_inverted_index.items():
        for position in positions:
            position_to_word[position] = word

    if not position_to_word:
        return ""

    words = [
        position_to_word[index]
        for index in sorted(position_to_word.keys())
    ]

    abstract = " ".join(words)

    abstract = abstract.replace(" ,", ",")
    abstract = abstract.replace(" .", ".")
    abstract = abstract.replace(" ;", ";")
    abstract = abstract.replace(" :", ":")
    abstract = abstract.replace("( ", "(")
    abstract = abstract.replace(" )", ")")

    return abstract.strip()


def clean_doi(doi):
    if not doi:
        return ""

    doi = str(doi).strip()

    doi = doi.replace("https://doi.org/", "")
    doi = doi.replace("http://doi.org/", "")

    return doi


def get_best_url(work):
    primary_location = work.get("primary_location") or {}
    landing_page_url = primary_location.get("landing_page_url")

    if landing_page_url:
        return landing_page_url

    open_access = work.get("open_access") or {}
    oa_url = open_access.get("oa_url")

    if oa_url:
        return oa_url

    ids = work.get("ids") or {}
    doi = ids.get("doi") or work.get("doi")

    if doi:
        return doi

    return work.get("id") or ""


def get_open_access_pdf_url(work):
    open_access = work.get("open_access") or {}
    primary_location = work.get("primary_location") or {}

    if primary_location.get("pdf_url"):
        return primary_location.get("pdf_url")

    best_oa_location = work.get("best_oa_location") or {}

    if best_oa_location.get("pdf_url"):
        return best_oa_location.get("pdf_url")

    if open_access.get("oa_url"):
        return open_access.get("oa_url")

    return ""


def get_authors(work, max_authors=6):
    authorships = work.get("authorships") or []

    authors = []

    for authorship in authorships[:max_authors]:
        author = authorship.get("author") or {}
        display_name = author.get("display_name")

        if display_name:
            authors.append(display_name)

    if len(authorships) > max_authors:
        authors.append("et al.")

    return authors


def get_venue(work):
    primary_location = work.get("primary_location") or {}
    source = primary_location.get("source") or {}

    venue = source.get("display_name")

    if venue:
        return venue

    host_venue = work.get("host_venue") or {}
    return host_venue.get("display_name") or ""


def normalize_openalex_work(work):
    ids = work.get("ids") or {}
    open_access = work.get("open_access") or {}

    title = work.get("title") or work.get("display_name") or "Untitled work"

    abstract = reconstruct_abstract(
        work.get("abstract_inverted_index")
    )

    doi = clean_doi(ids.get("doi") or work.get("doi"))

    return {
        "source": "OpenAlex",
        "openalex_id": work.get("id") or "",
        "title": title,
        "authors": get_authors(work),
        "year": work.get("publication_year"),
        "publication_date": work.get("publication_date") or "",
        "venue": get_venue(work),
        "doi": doi,
        "url": get_best_url(work),
        "pdf_url": get_open_access_pdf_url(work),
        "open_access": bool(open_access.get("is_oa")),
        "open_access_status": open_access.get("oa_status") or "",
        "type": work.get("type") or "",
        "cited_by_count": work.get("cited_by_count") or 0,
        "abstract": abstract,
        "concepts": [
            concept.get("display_name")
            for concept in (work.get("concepts") or [])[:5]
            if concept.get("display_name")
        ],
    }


def build_openalex_filter(from_year=None, to_year=None, open_access_only=False):
    filters = []

    if from_year:
        try:
            filters.append(f"from_publication_date:{int(from_year)}-01-01")
        except Exception:
            pass

    if to_year:
        try:
            filters.append(f"to_publication_date:{int(to_year)}-12-31")
        except Exception:
            pass

    if open_access_only:
        filters.append("is_oa:true")

    return ",".join(filters)


def clean_query(query):
    query = str(query or "").strip()

    query = re.sub(r"\s+", " ", query)

    return query


def search_openalex_works(
    query,
    limit=None,
    from_year=None,
    to_year=None,
    open_access_only=False,
):
    query = clean_query(query)

    if not query:
        raise ValueError("Search query is required.")

    limit = clamp_limit(limit)

    params = {
        "search": query,
        "per-page": limit,
        "sort": "relevance_score:desc",
    }

    filters = build_openalex_filter(
        from_year=from_year,
        to_year=to_year,
        open_access_only=open_access_only,
    )

    if filters:
        params["filter"] = filters

    if OPENALEX_MAILTO:
        params["mailto"] = OPENALEX_MAILTO

    response = requests.get(
        f"{OPENALEX_BASE_URL}/works",
        params=params,
        timeout=SCHOLAR_SEARCH_TIMEOUT,
    )

    response.raise_for_status()

    data = response.json()

    works = data.get("results") or []

    results = [
        normalize_openalex_work(work)
        for work in works
    ]

    return {
        "query": query,
        "source": "OpenAlex",
        "count": len(results),
        "results": results,
    }