import os
from urllib.parse import quote

import requests


GOOGLE_BOOKS_API_URL = (
    "https://www.googleapis.com/books/v1/volumes"
)

GOOGLE_BOOKS_TIMEOUT_SECONDS = 12


class GoogleBooksError(Exception):
    """Safe Google Books error for display in StudySource."""


def get_api_key():
    return os.getenv(
        "GOOGLE_BOOKS_API_KEY",
        "",
    ).strip()


def request_google_books(
    url=GOOGLE_BOOKS_API_URL,
    parameters=None,
):
    request_parameters = dict(
        parameters or {}
    )

    api_key = get_api_key()

    if api_key:
        request_parameters["key"] = api_key

    headers = {
        "Accept": "application/json",
        "User-Agent": "StudySource/1.0",
    }

    try:
        response = requests.get(
            url,
            params=request_parameters,
            headers=headers,
            timeout=GOOGLE_BOOKS_TIMEOUT_SECONDS,
        )
    except requests.Timeout as error:
        raise GoogleBooksError(
            "Google Books took too long to respond. "
            "Please try again."
        ) from error
    except requests.ConnectionError as error:
        raise GoogleBooksError(
            "StudySource could not connect to Google Books. "
            "Check your internet connection and try again."
        ) from error
    except requests.RequestException as error:
        raise GoogleBooksError(
            "An unexpected Google Books connection error occurred."
        ) from error

    if response.status_code == 404:
        raise GoogleBooksError(
            "The selected Google Books record could not be found."
        )

    if response.status_code == 429:
        raise GoogleBooksError(
            "Google Books temporarily limited this request. "
            "Please try again later."
        )

    if response.status_code >= 500:
        raise GoogleBooksError(
            "Google Books is temporarily unavailable. "
            "Please try again later."
        )

    if not response.ok:
        raise GoogleBooksError(
            "Google Books could not complete this request."
        )

    try:
        return response.json()
    except ValueError as error:
        raise GoogleBooksError(
            "Google Books returned an unreadable response."
        ) from error


def get_year(published_date):
    if not published_date:
        return None

    year_text = str(published_date)[:4]

    if year_text.isdigit():
        return int(year_text)

    return None


def normalize_volume(volume):
    volume_info = volume.get("volumeInfo") or {}
    access_info = volume.get("accessInfo") or {}

    volume_id = volume.get("id") or ""

    title = (
        volume_info.get("title")
        or ""
    ).strip()

    if not title:
        return None

    identifiers = volume_info.get(
        "industryIdentifiers"
    ) or []

    isbn = ""

    if identifiers:
        isbn = identifiers[0].get(
            "identifier",
            "",
        )

    external_id = volume_id

    if isbn:
        external_id = f"{volume_id}:{isbn}"

    source_url = (
        volume_info.get("infoLink")
        or f"https://books.google.com/books?id={volume_id}"
    )

    access_url = (
        access_info.get("previewLink")
        or source_url
    )

    publisher = (
        volume_info.get("publisher")
        or ""
    ).strip()

    return {
        "provider": "google_books",
        "external_id": external_id,
        "reference_type": "book",
        "title": title,
        "authors": volume_info.get(
            "authors"
        ) or [],
        "publication_year": get_year(
            volume_info.get("publishedDate")
        ),
        "doi": "",
        "description": (
            volume_info.get("description")
            or ""
        ),
        "source_name": publisher,
        "source_url": source_url,
        "open_access_url": access_url,
        "thumbnail_url": (
            volume_info.get("imageLinks", {})
            .get("thumbnail", "")
        ),
        "preview_available": bool(
            access_info.get("viewability")
            and access_info.get("viewability")
            != "NO_PAGES"
        ),
    }


def get_volume(external_id):
    volume_id = (
        external_id
        or ""
    ).strip().split(":", 1)[0]

    if not volume_id:
        raise GoogleBooksError(
            "The selected book has an invalid ID."
        )

    volume_url = (
        f"{GOOGLE_BOOKS_API_URL}/"
        f"{quote(volume_id)}"
    )

    volume_data = request_google_books(
        url=volume_url
    )

    result = normalize_volume(volume_data)

    if result is None:
        raise GoogleBooksError(
            "The selected Google Books record "
            "does not contain a title."
        )

    return result


def search_books(
    query,
    page=1,
    per_page=10,
):
    clean_query = (
        query
        or ""
    ).strip()

    if not clean_query:
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
        40,
    )

    response_data = request_google_books(
        parameters={
            "q": clean_query,
            "startIndex": (
                page - 1
            ) * per_page,
            "maxResults": per_page,
            "printType": "books",
        }
    )

    raw_items = response_data.get("items") or []
    results = []

    for item in raw_items:
        normalized = normalize_volume(item)

        if normalized:
            results.append(normalized)

    total_results = min(
        response_data.get("totalItems") or 0,
        1000000,
    )

    current_end = page * per_page

    return {
        "results": results,
        "total_results": total_results,
        "page": page,
        "per_page": per_page,
        "has_previous": page > 1,
        "has_next": current_end < total_results,
    }