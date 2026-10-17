import hashlib
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import (
    require_http_methods,
    require_POST,
)

from .forms import (
    EmailAuthenticationForm,
    ResearchFolderForm,
    SaveOpenAlexReferenceForm,
    SignUpForm,
)
from .models import (
    FolderReference,
    ResearchFolder,
    SavedReference,
    User,
)
from .services.openalex import (
    OpenAlexError,
    get_work,
    search_works,
)


def home(request):
    if request.user.is_authenticated:
        if request.user.role == User.Role.STUDENT:
            return redirect("student_dashboard")

    return render(
        request,
        "study/home.html",
    )


def about(request):
    if request.user.is_authenticated:
        if request.user.role == User.Role.STUDENT:
            return redirect("student_dashboard")

    return render(
        request,
        "study/about.html",
    )


@require_http_methods(["GET", "POST"])
def signup_view(request):
    if request.user.is_authenticated:
        return redirect("student_dashboard")

    if request.method == "POST":
        form = SignUpForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Your account was created successfully. "
                "Please log in.",
            )

            return redirect("login")
    else:
        form = SignUpForm()

    return render(
        request,
        "study/auth/signup.html",
        {
            "form": form,
        },
    )


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        if request.user.role == User.Role.STUDENT:
            return redirect("student_dashboard")

        return redirect("home")

    form = EmailAuthenticationForm(
        request=request,
        data=request.POST or None,
    )

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)

        messages.success(
            request,
            f"Welcome back, {user.full_name}.",
        )

        next_url = (
            request.POST.get("next")
            or request.GET.get("next")
        )

        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)

        if user.role == User.Role.STUDENT:
            return redirect("student_dashboard")

        return redirect("home")

    return render(
        request,
        "study/auth/login.html",
        {
            "form": form,
            "next": request.GET.get("next", ""),
        },
    )


@login_required
def student_dashboard(request):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied

    recent_folders = (
        request.user.research_folders
        .annotate(
            reference_count=Count(
                "folder_references"
            )
        )
        .all()[:3]
    )

    context = {
        "folder_count": (
            request.user
            .research_folders
            .count()
        ),
        "reference_count": (
            request.user
            .saved_references
            .count()
        ),
        "note_count": 0,
        "upcoming_deadline_count": 0,
        "recent_folders": recent_folders,
    }

    return render(
        request,
        "study/dashboard.html",
        context,
    )


@login_required
def paper_search(request):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied

    query = request.GET.get(
        "q",
        "",
    ).strip()

    requested_page = request.GET.get(
        "page",
        "1",
    )

    try:
        page = max(
            1,
            int(requested_page),
        )
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
        "folders": (
            request.user
            .research_folders
            .all()
        ),
    }

    if not query:
        return render(
            request,
            "study/references/paper_search.html",
            context,
        )

    context["search_performed"] = True

    if len(query) < 2:
        context["search_error"] = (
            "Enter at least two characters to search."
        )

        return render(
            request,
            "study/references/paper_search.html",
            context,
        )

    if len(query) > 200:
        context["search_error"] = (
            "The search term must be "
            "200 characters or fewer."
        )

        return render(
            request,
            "study/references/paper_search.html",
            context,
        )

    cache_source = (
        f"{query.lower()}:{page}:10"
    )

    cache_digest = hashlib.sha256(
        cache_source.encode("utf-8")
    ).hexdigest()

    cache_key = (
        f"openalex-paper-search:"
        f"{cache_digest}"
    )

    search_data = cache.get(cache_key)

    if search_data is None:
        try:
            search_data = search_works(
                query=query,
                page=page,
                per_page=10,
            )
        except OpenAlexError as error:
            context["search_error"] = str(error)

            return render(
                request,
                "study/references/paper_search.html",
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
        "study/references/paper_search.html",
        context,
    )


def redirect_to_paper_search(request):
    """
    Return the student to the same OpenAlex search.

    The browser only supplies navigation information here.
    Paper metadata is retrieved again from OpenAlex.
    """

    query = request.POST.get(
        "return_query",
        "",
    ).strip()[:200]

    requested_page = request.POST.get(
        "return_page",
        "1",
    )

    try:
        page = max(
            1,
            int(requested_page),
        )
    except (TypeError, ValueError):
        page = 1

    parameters = {}

    if query:
        parameters["q"] = query
        parameters["page"] = page

    search_url = reverse("paper_search")

    if parameters:
        search_url = (
            f"{search_url}?"
            f"{urlencode(parameters)}"
        )

    return redirect(search_url)


@require_POST
@login_required
def save_openalex_reference(request):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied

    form = SaveOpenAlexReferenceForm(
        request.POST,
        owner=request.user,
    )

    if not form.is_valid():
        messages.error(
            request,
            "The selected paper could not be saved. "
            "Please try again.",
        )

        return redirect_to_paper_search(
            request
        )

    external_id = form.cleaned_data[
        "external_id"
    ]

    selected_folder = form.cleaned_data[
        "folder"
    ]

    try:
        paper_data = get_work(
            external_id
        )
    except OpenAlexError as error:
        messages.error(
            request,
            str(error),
        )

        return redirect_to_paper_search(
            request
        )

    doi = (
        paper_data.get("doi")
        or ""
    ).strip()

    with transaction.atomic():
        saved_reference = (
            SavedReference.objects.filter(
                owner=request.user,
                provider=(
                    SavedReference
                    .Provider
                    .OPENALEX
                ),
                external_id=external_id,
            )
            .first()
        )

        if (
            saved_reference is None
            and doi
        ):
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
                    provider=(
                        SavedReference
                        .Provider
                        .OPENALEX
                    ),
                    external_id=external_id,
                    reference_type=(
                        SavedReference
                        .ReferenceType
                        .PAPER
                    ),
                    title=(
                        paper_data["title"][:500]
                    ),
                    authors=(
                        paper_data.get("authors")
                        or []
                    ),
                    publication_year=(
                        paper_data.get(
                            "publication_year"
                        )
                    ),
                    doi=doi[:255],
                    description=(
                        paper_data.get(
                            "description"
                        )
                        or ""
                    ),
                    source_name=(
                        paper_data.get(
                            "source_name"
                        )
                        or ""
                    )[:255],
                    source_url=(
                        paper_data.get(
                            "source_url"
                        )
                        or ""
                    )[:1000],
                    access_url=(
                        paper_data.get(
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
                FolderReference.objects
                .get_or_create(
                    folder=selected_folder,
                    saved_reference=saved_reference,
                )
            )

    if reference_created and selected_folder:
        messages.success(
            request,
            f'"{saved_reference.title}" was saved '
            f'to "{selected_folder.name}".',
        )
    elif reference_created:
        messages.success(
            request,
            f'"{saved_reference.title}" was saved '
            f"to Saved References.",
        )
    elif (
        selected_folder
        and folder_link_created
    ):
        messages.success(
            request,
            f'The existing reference was added '
            f'to "{selected_folder.name}".',
        )
    elif selected_folder:
        messages.info(
            request,
            "This reference is already saved "
            "in the selected folder.",
        )
    else:
        messages.info(
            request,
            "This reference is already in "
            "Saved References.",
        )

    return redirect_to_paper_search(
        request
    )


@login_required
def saved_reference_list(request):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied

    search_query = request.GET.get(
        "q",
        "",
    ).strip()

    references = (
        SavedReference.objects
        .filter(owner=request.user)
        .prefetch_related("folders")
    )

    if search_query:
        references = references.filter(
            Q(title__icontains=search_query)
            | Q(doi__icontains=search_query)
            | Q(
                source_name__icontains=
                search_query
            )
        )

    context = {
        "references": references,
        "search_query": search_query,
    }

    return render(
        request,
        "study/references/saved_reference_list.html",
        context,
    )


@login_required
def folder_list(request):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied

    folders = (
        ResearchFolder.objects
        .filter(owner=request.user)
        .annotate(
            reference_count=Count(
                "folder_references"
            )
        )
    )

    return render(
        request,
        "study/folders/folder_list.html",
        {
            "folders": folders,
        },
    )


@login_required
def folder_detail(request, folder_id):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied

    folder = get_object_or_404(
        ResearchFolder,
        id=folder_id,
        owner=request.user,
    )

    folder_references = (
        FolderReference.objects
        .filter(folder=folder)
        .select_related(
            "saved_reference"
        )
    )

    context = {
        "folder": folder,
        "folder_references": folder_references,
        "reference_count": (
            folder_references.count()
        ),
        "note_count": 0,
        "image_count": 0,
        "deadline_count": 0,
    }

    return render(
        request,
        "study/folders/folder_detail.html",
        context,
    )


@login_required
@require_http_methods(["GET", "POST"])
def folder_create(request):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied

    if request.method == "POST":
        form = ResearchFolderForm(
            request.POST,
            owner=request.user,
        )

        if form.is_valid():
            folder = form.save(
                commit=False
            )

            folder.owner = request.user
            folder.save()

            messages.success(
                request,
                f'"{folder.name}" was created '
                f"successfully.",
            )

            return redirect(
                "folder_detail",
                folder_id=folder.id,
            )
    else:
        form = ResearchFolderForm(
            owner=request.user
        )

    return render(
        request,
        "study/folders/folder_form.html",
        {
            "form": form,
            "page_title": (
                "Create research folder"
            ),
            "submit_label": "Create folder",
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def folder_update(request, folder_id):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied

    folder = get_object_or_404(
        ResearchFolder,
        id=folder_id,
        owner=request.user,
    )

    if request.method == "POST":
        form = ResearchFolderForm(
            request.POST,
            instance=folder,
            owner=request.user,
        )

        if form.is_valid():
            folder = form.save()

            messages.success(
                request,
                f'"{folder.name}" was updated '
                f"successfully.",
            )

            return redirect(
                "folder_detail",
                folder_id=folder.id,
            )
    else:
        form = ResearchFolderForm(
            instance=folder,
            owner=request.user,
        )

    return render(
        request,
        "study/folders/folder_form.html",
        {
            "form": form,
            "folder": folder,
            "page_title": (
                "Edit research folder"
            ),
            "submit_label": "Save changes",
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def folder_delete(request, folder_id):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied

    folder = get_object_or_404(
        ResearchFolder,
        id=folder_id,
        owner=request.user,
    )

    if request.method == "POST":
        folder_name = folder.name
        folder.delete()

        messages.success(
            request,
            f'"{folder_name}" was deleted '
            f"successfully.",
        )

        return redirect("folder_list")

    return render(
        request,
        "study/folders/folder_confirm_delete.html",
        {
            "folder": folder,
        },
    )


@require_POST
@login_required
def logout_view(request):
    logout(request)

    messages.success(
        request,
        "You have been logged out.",
    )

    return redirect("home")