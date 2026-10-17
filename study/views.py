from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import (
    require_http_methods,
    require_POST,
)

from .forms import (
    EmailAuthenticationForm,
    ResearchFolderForm,
    SignUpForm,
)
from .models import ResearchFolder, User


def home(request):
    if request.user.is_authenticated:
        if request.user.role == User.Role.STUDENT:
            return redirect("student_dashboard")

    return render(request, "study/home.html")


def about(request):
    if request.user.is_authenticated:
        if request.user.role == User.Role.STUDENT:
            return redirect("student_dashboard")

    return render(request, "study/about.html")


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
        {"form": form},
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

    recent_folders = request.user.research_folders.all()[:3]

    context = {
        "folder_count": request.user.research_folders.count(),
        "reference_count": 0,
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
def folder_list(request):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied

    folders = ResearchFolder.objects.filter(
        owner=request.user
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

    context = {
        "folder": folder,
        "reference_count": 0,
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
            folder = form.save(commit=False)
            folder.owner = request.user
            folder.save()

            messages.success(
                request,
                f'"{folder.name}" was created successfully.',
            )
            return redirect(
                "folder_detail",
                folder_id=folder.id,
            )
    else:
        form = ResearchFolderForm(owner=request.user)

    return render(
        request,
        "study/folders/folder_form.html",
        {
            "form": form,
            "page_title": "Create research folder",
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
                f'"{folder.name}" was updated successfully.',
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
            "page_title": "Edit research folder",
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
            f'"{folder_name}" was deleted successfully.',
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