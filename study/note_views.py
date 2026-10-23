from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.views.decorators.http import (
    require_http_methods,
)

from .models import (
    ResearchFolder,
    ResearchNote,
    User,
)
from .note_forms import ResearchNoteForm


def require_student(request):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied


@login_required
def note_list(request):
    require_student(request)

    notes = (
        ResearchNote.objects
        .filter(owner=request.user)
        .select_related(
            "folder",
            "saved_reference",
        )
    )

    folder_id = request.GET.get("folder")

    if folder_id:
        notes = notes.filter(
            folder_id=folder_id
        )

    folders = (
        request.user
        .research_folders
        .all()
    )

    return render(
        request,
        "study/notes/note_list.html",
        {
            "notes": notes,
            "folders": folders,
            "selected_folder": folder_id,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def note_create(request, folder_id):
    require_student(request)

    folder = get_object_or_404(
        ResearchFolder,
        id=folder_id,
        owner=request.user,
    )

    if request.method == "POST":
        form = ResearchNoteForm(
            request.POST,
            owner=request.user,
        )

        if form.is_valid():
            note = form.save(
                commit=False
            )

            note.owner = request.user
            note.folder = folder
            note.save()

            messages.success(
                request,
                f'"{note.title}" was created.',
            )

            return redirect(
                "note_detail",
                note_id=note.id,
            )
    else:
        form = ResearchNoteForm(
            owner=request.user,
        )

    return render(
        request,
        "study/notes/note_form.html",
        {
            "form": form,
            "folder": folder,
            "page_title": "Create research note",
            "submit_label": "Create note",
        },
    )


@login_required
def note_detail(request, note_id):
    require_student(request)

    note = get_object_or_404(
        ResearchNote.objects.select_related(
            "folder",
            "saved_reference",
        ),
        id=note_id,
        owner=request.user,
    )

    return render(
        request,
        "study/notes/note_detail.html",
        {
            "note": note,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def note_update(request, note_id):
    require_student(request)

    note = get_object_or_404(
        ResearchNote,
        id=note_id,
        owner=request.user,
    )

    if request.method == "POST":
        form = ResearchNoteForm(
            request.POST,
            instance=note,
            owner=request.user,
        )

        if form.is_valid():
            note = form.save()

            messages.success(
                request,
                f'"{note.title}" was updated.',
            )

            return redirect(
                "note_detail",
                note_id=note.id,
            )
    else:
        form = ResearchNoteForm(
            instance=note,
            owner=request.user,
        )

    return render(
        request,
        "study/notes/note_form.html",
        {
            "form": form,
            "folder": note.folder,
            "note": note,
            "page_title": "Edit research note",
            "submit_label": "Save changes",
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def note_delete(request, note_id):
    require_student(request)

    note = get_object_or_404(
        ResearchNote,
        id=note_id,
        owner=request.user,
    )

    if request.method == "POST":
        note_title = note.title
        folder_id = note.folder_id

        note.delete()

        messages.success(
            request,
            f'"{note_title}" was deleted.',
        )

        return redirect(
            "folder_detail",
            folder_id=folder_id,
        )

    return render(
        request,
        "study/notes/note_confirm_delete.html",
        {
            "note": note,
        },
    )