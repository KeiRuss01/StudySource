import os
import re
from html import unescape
from urllib.parse import quote

import requests


CROSSREF_API_URL = "https://api.crossref.org/works"
CROSSREF_TIMEOUT_SECONDS = 12


class CrossrefError(Exception):
    """Safe Crossref error for display in StudySource."""


def clean_html(value):
    if not value:
        return ""

    text = re.sub(
        r"<[^>]+>",
        " ",
        value,
    )

    text = unescape(text)

    return " ".join(text.split())


def normalize_doi(value):
    return (
        value
        or ""
    ).strip().lower().replace(
        "https://doi.org/",
        "",
    ).replace(
        "http://doi.org/",
        "",
    ).strip()


def get_year(message):
    for key in (
        "published-print",
        "published-online",
        "issued",
        "created",
    ):
        date_data = message.get(key) or {}
        date_parts = date_data.get("date-parts") or []

        if date_parts and date_parts[0]:
            return date_parts[0][0]

    return None


def get_authors(message):
    authors = []

    for author in message.get("author") or []:
        given = (author.get("given") or "").strip()
        family = (author.get("family") or "").strip()

        full_name = " ".join(
            part
            for part in (given, family)
            if part
        )

        if full_name:
            authors.append(full_name)

    return authors


def request_crossref(doi):
    clean_doi = normalize_doi(doi)

    if not clean_doi:
        raise CrossrefError(
            "Enter a DOI to look up."
        )

    url = f"{CROSSREF_API_URL}/{quote(clean_doi)}"

    headers = {
        "Accept": "application/json",
        "User-Agent": (
            "StudySource/1.0 "
            f"(mailto:{os.getenv('CROSSREF_EMAIL', '')})"
        ),
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=CROSSREF_TIMEOUT_SECONDS,
        )
    except requests.Timeout as error:
        raise CrossrefError(
            "Crossref took too long to respond. "
            "Please try again."
        ) from error
    except requests.ConnectionError as error:
        raise CrossrefError(
            "StudySource could not connect to Crossref. "
            "Check your internet connection and try again."
        ) from error
    except requests.RequestException as error:
        raise CrossrefError(
            "An unexpected Crossref connection error occurred."
        ) from error

    if response.status_code == 404:
        raise CrossrefError(
            "Crossref could not find a record for that DOI."
        )

    if response.status_code == 429:
        raise CrossrefError(
            "Crossref temporarily limited this request. "
            "Please try again later."
        )

    if response.status_code >= 500:
        raise CrossrefError(
            "Crossref is temporarily unavailable. "
            "Please try again later."
        )

    if not response.ok:
        raise CrossrefError(
            "Crossref could not complete this DOI lookup."
        )

    try:
        return response.json()
    except ValueError as error:
        raise CrossrefError(
            "Crossref returned an unreadable response."
        ) from error


def lookup_doi(doi):
    response_data = request_crossref(doi)
    message = response_data.get("message") or {}

    clean_doi = normalize_doi(
        message.get("DOI") or doi
    )

    titles = message.get("title") or []
    title = titles[0].strip() if titles else ""

    if not title:
        raise CrossrefError(
            "Crossref returned a record without a title."
        )

    item_type = (
        message.get("type")
        or ""
    ).lower()

    reference_type = (
        "book"
        if "book" in item_type
        else "paper"
    )

    source_name = ""
    containers = message.get("container-title") or []

    if containers:
        source_name = containers[0]

    source_url = (
        message.get("URL")
        or f"https://doi.org/{clean_doi}"
    )

    return {
        "provider": "crossref",
        "external_id": clean_doi,
        "reference_type": reference_type,
        "title": title,
        "authors": get_authors(message),
        "publication_year": get_year(message),
        "doi": clean_doi,
        "description": clean_html(
            message.get("abstract")
        ),
        "source_name": source_name,
        "source_url": source_url,
        "open_access_url": "",
        "is_open_access": False,
    }