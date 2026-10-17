import os
import re

import requests


OPENALEX_API_BASE_URL = "https://api.openalex.org"
OPENALEX_WORKS_URL = f"{OPENALEX_API_BASE_URL}/works"
OPENALEX_TIMEOUT_SECONDS = 12

OPENALEX_ID_PATTERN = re.compile(r"^W\d+$")


class OpenAlexError(Exception):
    """A safe error that can be displayed in StudySource."""


def get_api_key():
    """Return the configured OpenAlex API key."""

    api_key = os.getenv(
        "OPENALEX_API_KEY",
        "",
    ).strip()

    if not api_key:
        raise OpenAlexError(
            "OpenAlex is not configured. Add "
            "OPENALEX_API_KEY to the environment file."
        )

    return api_key


def request_openalex(url, parameters=None):
    """
    Send a request to OpenAlex and handle common errors.

    The API key is added on the Django server and is never
    exposed to the browser.
    """

    request_parameters = dict(parameters or {})

    request_parameters["api_key"] = get_api_key()

    headers = {
        "Accept": "application/json",
        "User-Agent": "StudySource/1.0",
    }

    try:
        response = requests.get(
            url,
            params=request_parameters,
            headers=headers,
            timeout=OPENALEX_TIMEOUT_SECONDS,
        )
    except requests.Timeout as error:
        raise OpenAlexError(
            "OpenAlex took too long to respond. "
            "Please try again."
        ) from error
    except requests.ConnectionError as error:
        raise OpenAlexError(
            "StudySource could not connect to OpenAlex. "
            "Check your internet connection and try again."
        ) from error
    except requests.RequestException as error:
        raise OpenAlexError(
            "An unexpected OpenAlex connection error occurred."
        ) from error

    if response.status_code in {401, 403}:
        raise OpenAlexError(
            "The OpenAlex API key was rejected. "
            "Check that the key is correct and activated."
        )

    if response.status_code == 404:
        raise OpenAlexError(
            "The selected OpenAlex paper could not be found."
        )

    if response.status_code == 429:
        raise OpenAlexError(
            "The OpenAlex usage limit has been reached. "
            "Please wait before trying again."
        )

    if response.status_code >= 500:
        raise OpenAlexError(
            "OpenAlex is temporarily unavailable. "
            "Please try again later."
        )

    if not response.ok:
        raise OpenAlexError(
            "OpenAlex could not complete this request."
        )

    try:
        return response.json()
    except ValueError as error:
        raise OpenAlexError(
            "OpenAlex returned an unreadable response."
        ) from error


def rebuild_abstract(inverted_index):
    """
    Convert OpenAlex's inverted abstract format into text.

    OpenAlex stores abstract words mapped to their original
    positions. This restores those words to reading order.
    """

    if not inverted_index:
        return None

    positioned_words = []

    for word, positions in inverted_index.items():
        for position in positions:
            positioned_words.append(
                (position, word)
            )

    positioned_words.sort(
        key=lambda item: item[0]
    )

    abstract = " ".join(
        word
        for _, word in positioned_words
    ).strip()

    return abstract or None


def get_authors(work):
    """Return the available author names."""

    authors = []

    for authorship in work.get("authorships") or []:
        author = authorship.get("author") or {}
        display_name = author.get("display_name")

        if display_name:
            authors.append(display_name)

    return authors


def get_source_name(work):
    """Return the publication source name if provided."""

    primary_location = (
        work.get("primary_location")
        or {}
    )

    source = (
        primary_location.get("source")
        or {}
    )

    return source.get("display_name")


def get_source_url(work):
    """
    Return the best available original source URL.

    The publisher landing page is preferred. A DOI link or
    OpenAlex record is used when no publisher page exists.
    """

    primary_location = (
        work.get("primary_location")
        or {}
    )

    landing_page_url = primary_location.get(
        "landing_page_url"
    )

    if landing_page_url:
        return landing_page_url

    doi = work.get("doi")

    if doi:
        return doi

    return work.get("id")


def get_open_access_url(work):
    """Return an available open-access or PDF URL."""

    best_oa_location = (
        work.get("best_oa_location")
        or {}
    )

    return (
        best_oa_location.get("pdf_url")
        or best_oa_location.get(
            "landing_page_url"
        )
    )


def normalize_doi(doi):
    """Remove the URL prefix while keeping the DOI value."""

    if not doi:
        return None

    return (
        doi.replace(
            "https://doi.org/",
            "",
        )
        .replace(
            "http://doi.org/",
            "",
        )
        .strip()
    )


def normalize_work(work):
    """
    Convert one OpenAlex work into StudySource fields.

    Missing information remains None instead of being invented.
    """

    openalex_id = work.get("id")

    if openalex_id:
        external_id = (
            openalex_id
            .rstrip("/")
            .split("/")[-1]
        )
    else:
        external_id = None

    open_access = (
        work.get("open_access")
        or {}
    )

    return {
        "provider": "openalex",
        "external_id": external_id,
        "reference_type": work.get("type"),
        "title": (
            work.get("display_name")
            or work.get("title")
        ),
        "authors": get_authors(work),
        "publication_year": work.get(
            "publication_year"
        ),
        "source_name": get_source_name(work),
        "description": rebuild_abstract(
            work.get(
                "abstract_inverted_index"
            )
        ),
        "doi": normalize_doi(
            work.get("doi")
        ),
        "source_url": get_source_url(work),
        "open_access_url": get_open_access_url(
            work
        ),
        "is_open_access": bool(
            open_access.get("is_oa")
        ),
        "cited_by_count": work.get(
            "cited_by_count"
        ),
    }


def search_works(
    query,
    page=1,
    per_page=10,
):
    """
    Search OpenAlex for scholarly works.

    Returns normalized results and pagination information.
    """

    cleaned_query = (
        query
        or ""
    ).strip()

    if not cleaned_query:
        return {
            "results": [],
            "total_results": 0,
            "page": 1,
            "per_page": per_page,
            "has_previous": False,
            "has_next": False,
        }

    try:
        page = max(
            1,
            int(page),
        )
    except (TypeError, ValueError):
        page = 1

    try:
        per_page = int(per_page)
    except (TypeError, ValueError):
        per_page = 10

    per_page = min(
        max(per_page, 1),
        25,
    )

    parameters = {
        "search": cleaned_query,
        "page": page,
        "per-page": per_page,
    }

    response_data = request_openalex(
        OPENALEX_WORKS_URL,
        parameters,
    )

    raw_results = (
        response_data.get("results")
        or []
    )

    metadata = (
        response_data.get("meta")
        or {}
    )

    results = [
        normalize_work(work)
        for work in raw_results
    ]

    total_results = (
        metadata.get("count")
        or 0
    )

    current_end = page * per_page

    return {
        "results": results,
        "total_results": total_results,
        "page": page,
        "per_page": per_page,
        "has_previous": page > 1,
        "has_next": (
            current_end < total_results
        ),
    }


def get_work(external_id):
    """
    Fetch one trusted OpenAlex work by its external ID.

    Only an OpenAlex ID such as W2741809807 is accepted.
    Metadata sent by a browser is never trusted for saving.
    """

    cleaned_external_id = (
        external_id
        or ""
    ).strip()

    if not OPENALEX_ID_PATTERN.fullmatch(
        cleaned_external_id
    ):
        raise OpenAlexError(
            "The selected paper has an invalid OpenAlex ID."
        )

    work_url = (
        f"{OPENALEX_WORKS_URL}/"
        f"{cleaned_external_id}"
    )

    response_data = request_openalex(
        work_url
    )

    normalized_work = normalize_work(
        response_data
    )

    if not normalized_work.get("title"):
        raise OpenAlexError(
            "The selected paper does not contain a title "
            "and cannot be saved."
        )

    return normalized_work