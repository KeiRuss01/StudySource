from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseRedirect

from .deadline_forms import ResearchDeadlineForm
from .models import CalendarConnection, ResearchDeadline, ResearchFolder, User
from .services.google_calendar import (
    GoogleCalendarError,
    access_token,
    authorization_url,
    configured,
    exchange_code,
    sync_deadline,
)


def require_student(request):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied


@login_required
def calendar_connect(request):
    require_student(request)
    if not configured():
        messages.error(request, "Google Calendar credentials are not configured yet.")
        return redirect("deadline_list")
    if not request.session.session_key:
        request.session.create()
    state = request.session.session_key
    request.session["calendar_oauth_state"] = state
    return HttpResponseRedirect(authorization_url(state))


@login_required
def calendar_callback(request):
    require_student(request)
    if request.GET.get("state") != request.session.get("calendar_oauth_state"):
        messages.error(request, "Google Calendar authorization could not be verified.")
        return redirect("deadline_list")
    try:
        data = exchange_code(request.GET["code"])
        from django.utils import timezone
        from datetime import timedelta
        CalendarConnection.objects.update_or_create(
            owner=request.user,
            defaults={
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token", ""),
                "token_expires_at": timezone.now() + timedelta(seconds=int(data.get("expires_in", 3600)) - 60),
            },
        )
        messages.success(request, "Google Calendar connected successfully.")
    except (KeyError, GoogleCalendarError):
        messages.error(request, "Google Calendar authorization failed.")
    return redirect("deadline_list")


@login_required
@require_http_methods(["POST"])
def calendar_disconnect(request):
    require_student(request)
    CalendarConnection.objects.filter(owner=request.user).delete()
    messages.success(request, "Google Calendar disconnected.")
    return redirect("deadline_list")


@login_required
@require_http_methods(["POST"])
def deadline_sync(request, deadline_id):
    require_student(request)
    deadline = get_object_or_404(ResearchDeadline, id=deadline_id, owner=request.user)
    connection = getattr(request.user, "calendar_connection", None)
    if connection is None:
        messages.error(request, "Connect Google Calendar before syncing a deadline.")
        return redirect("deadline_list")
    try:
        deadline.google_event_id = sync_deadline(connection, deadline)
        deadline.save(update_fields=["google_event_id", "updated_at"])
        messages.success(request, f'"{deadline.title}" was synced to Google Calendar.')
    except GoogleCalendarError as error:
        messages.error(request, str(error))
    return redirect("deadline_list")


@login_required
def deadline_list(request):
    require_student(request)
    deadlines = ResearchDeadline.objects.filter(
        owner=request.user
    ).select_related("folder")
    return render(request, "study/deadlines/deadline_list.html", {
        "deadlines": deadlines,
    })


@login_required
@require_http_methods(["GET", "POST"])
def deadline_create(request, folder_id=None):
    require_student(request)
    folder = None
    if folder_id is not None:
        folder = get_object_or_404(
            ResearchFolder, id=folder_id, owner=request.user
        )
    if request.method == "POST":
        form = ResearchDeadlineForm(request.POST, owner=request.user)
        if form.is_valid():
            deadline = form.save(commit=False)
            deadline.owner = request.user
            deadline.folder = folder or form.cleaned_data["folder"]
            deadline.save()
            messages.success(request, f'"{deadline.title}" was created.')
            return redirect("deadline_list")
    else:
        form = ResearchDeadlineForm(
            initial={"folder": folder} if folder else None,
            owner=request.user,
        )
    return render(request, "study/deadlines/deadline_form.html", {
        "form": form,
        "folder": folder,
        "folders": request.user.research_folders.all(),
        "page_title": "Create deadline",
        "submit_label": "Create deadline",
    })


@login_required
@require_http_methods(["GET", "POST"])
def deadline_update(request, deadline_id):
    require_student(request)
    deadline = get_object_or_404(
        ResearchDeadline, id=deadline_id, owner=request.user
    )
    if request.method == "POST":
        form = ResearchDeadlineForm(
            request.POST, instance=deadline, owner=request.user
        )
        if form.is_valid():
            deadline = form.save()
            messages.success(request, f'"{deadline.title}" was updated.')
            return redirect("deadline_list")
    else:
        form = ResearchDeadlineForm(instance=deadline, owner=request.user)
    return render(request, "study/deadlines/deadline_form.html", {
        "form": form,
        "folder": deadline.folder,
        "folders": request.user.research_folders.all(),
        "deadline": deadline,
        "page_title": "Edit deadline",
        "submit_label": "Save changes",
    })


@login_required
@require_http_methods(["GET", "POST"])
def deadline_delete(request, deadline_id):
    require_student(request)
    deadline = get_object_or_404(
        ResearchDeadline, id=deadline_id, owner=request.user
    )
    if request.method == "POST":
        title = deadline.title
        deadline.delete()
        messages.success(request, f'"{title}" was deleted.')
        return redirect("deadline_list")
    return render(request, "study/deadlines/deadline_confirm_delete.html", {
        "deadline": deadline,
    })
