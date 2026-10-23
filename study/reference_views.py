import hashlib
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import (
    FolderReference,
    SavedReference,
    User,
)
from .reference_forms import SaveExternalReferenceForm
from .services.crossref import (
    CrossrefError,
    lookup_doi,
)
from .services.google_books import (
    GoogleBooksError,
    get_volume,
    search_books,
)


def require_student(request):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied


def build_cache_key(prefix, value, page=None):
    source = f"{value.lower()}:{page or ''}"

    digest = hashlib.sha256(
        source.encode("utf-8")
    ).hexdigest()

    return f"{prefix}:{digest}"


def redirect_after_save(request):
    provider = request.POST.get(
        "return_provider",
        "paper",
    )

    if provider == "book":
        query = request.POST.get(
            "return_query",
            "",
        ).strip()

        page = request.POST.get(
            "return_page",
            "1",
        )

        parameters = {}

        if query:
            parameters["q"] = query
            parameters["page"] = page

        url = reverse("book_search")

        if parameters:
            url = f"{url}?{urlencode(parameters)}"

        return redirect(url)

    if provider == "doi":
        doi = request.POST.get(
            "return_doi",
            "",
        ).strip()

        url = reverse("doi_lookup")

        if doi:
            url = f"{url}?{urlencode({'doi': doi})}"

        return redirect(url)

    return redirect(
        "paper_search",
    )


@login_required
def book_search(request):
    require_student(request)

    query = request.GET.get(
        "q",
        "",
    ).strip()

    requested_page = request.GET.get(
        "page",
        "1",
    )

    try:
        page = max(1, int(requested_page))
    except (TypeError, ValueError):
        page = 1

    context = {
        "query": query,
        "results": [],
        "total_results": 0,
        "page": page,
        "has_previous": False,
        "has_next": False,
        "search_performed": False,
        "search_error": None,
        "folders": request.user.research_folders.all(),
    }

    if not query:
        return render(
            request,
            "study/references/book_search.html",
            context,
        )

    context["search_performed"] = True

    if len(query) < 2:
        context["search_error"] = (
            "Enter at least two characters to search."
        )

        return render(
            request,
            "study/references/book_search.html",
            context,
        )

    cache_key = build_cache_key(
        "google-books-search",
        query,
        page,
    )

    search_data = cache.get(cache_key)

    if search_data is None:
        try:
            search_data = search_books(
                query=query,
                page=page,
                per_page=10,
            )
        except GoogleBooksError as error:
            context["search_error"] = str(error)

            return render(
                request,
                "study/references/book_search.html",
                context,
            )

        cache.set(
            cache_key,
            search_data,
            timeout=300,
        )

    context.update(search_data)

    return render(
        request,
        "study/references/book_search.html",
        context,
    )


@login_required
def doi_lookup(request):
    require_student(request)

    doi = request.GET.get(
        "doi",
        "",
    ).strip()

    context = {
        "doi": doi,
        "result": None,
        "lookup_performed": False,
        "lookup_error": None,
        "folders": request.user.research_folders.all(),
    }

    if not doi:
        return render(
            request,
            "study/references/doi_lookup.html",
            context,
        )

    context["lookup_performed"] = True

    cache_key = build_cache_key(
        "crossref-doi",
        doi,
    )

    result = cache.get(cache_key)

    if result is None:
        try:
            result = lookup_doi(doi)
        except CrossrefError as error:
            context["lookup_error"] = str(error)

            return render(
                request,
                "study/references/doi_lookup.html",
                context,
            )

        cache.set(
            cache_key,
            result,
            timeout=900,
        )

    context["result"] = result

    return render(
        request,
        "study/references/doi_lookup.html",
        context,
    )


@require_POST
@login_required
def save_external_reference(request):
    require_student(request)

    form = SaveExternalReferenceForm(
        request.POST,
        owner=request.user,
    )

    if not form.is_valid():
        messages.error(
            request,
            "The selected reference could not be saved.",
        )

        return redirect_after_save(request)

    provider = form.cleaned_data["provider"]
    external_id = form.cleaned_data["external_id"]
    selected_folder = form.cleaned_data["folder"]

    try:
        if provider == "crossref":
            reference_data = lookup_doi(external_id)
        else:
            reference_data = get_volume(external_id)
    except (CrossrefError, GoogleBooksError) as error:
        messages.error(request, str(error))

        return redirect_after_save(request)

    doi = (
        reference_data.get("doi")
        or ""
    ).strip()

    with transaction.atomic():
        saved_reference = (
            SavedReference.objects.filter(
                owner=request.user,
                provider=provider,
                external_id=external_id,
            )
            .first()
        )

        if saved_reference is None and doi:
            saved_reference = (
                SavedReference.objects.filter(
                    owner=request.user,
                    doi__iexact=doi,
                )
                .first()
            )

        reference_created = False

        if saved_reference is None:
            saved_reference = (
                SavedReference.objects.create(
                    owner=request.user,
                    provider=provider,
                    external_id=external_id,
                    reference_type=(
                        SavedReference
                        .ReferenceType
                        .BOOK
                        if provider == "google_books"
                        else SavedReference
                        .ReferenceType
                        .PAPER
                    ),
                    title=(
                        reference_data["title"][:500]
                    ),
                    authors=(
                        reference_data.get("authors")
                        or []
                    ),
                    publication_year=(
                        reference_data.get(
                            "publication_year"
                        )
                    ),
                    doi=doi[:255],
                    description=(
                        reference_data.get(
                            "description"
                        )
                        or ""
                    ),
                    source_name=(
                        reference_data.get(
                            "source_name"
                        )
                        or ""
                    )[:255],
                    source_url=(
                        reference_data.get(
                            "source_url"
                        )
                        or ""
                    )[:1000],
                    access_url=(
                        reference_data.get(
                            "open_access_url"
                        )
                        or ""
                    )[:1000],
                )
            )

            reference_created = True

        folder_link_created = False

        if selected_folder:
            _, folder_link_created = (
                FolderReference.objects.get_or_create(
                    folder=selected_folder,
                    saved_reference=saved_reference,
                )
            )

    if selected_folder and folder_link_created:
        messages.success(
            request,
            f'"{saved_reference.title}" was added '
            f'to "{selected_folder.name}".',
        )
    elif reference_created:
        messages.success(
            request,
            f'"{saved_reference.title}" was saved '
            "to Saved References.",
        )
    else:
        messages.info(
            request,
            "This reference is already saved.",
        )

    return redirect_after_save(request)