from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import (
    ResearchDeadline,
    ResearchFolder,
    ResearchImage,
    ResearchNote,
    SavedReference,
    User,
)


def require_admin(request):
    if request.user.role != User.Role.ADMIN:
        raise PermissionDenied


@login_required
def admin_dashboard(request):
    require_admin(request)

    students = User.objects.filter(role=User.Role.STUDENT)

    return render(
        request,
        "study/admin/dashboard.html",
        {
            "student_count": students.count(),
            "active_student_count": students.filter(is_active=True).count(),
            "folder_count": ResearchFolder.objects.count(),
            "reference_count": SavedReference.objects.count(),
            "note_count": ResearchNote.objects.count(),
            "deadline_count": ResearchDeadline.objects.count(),
            "image_count": ResearchImage.objects.count(),
            "recent_students": students.order_by("-created_at")[:6],
            "recent_folders": ResearchFolder.objects.select_related(
                "owner"
            ).order_by("-created_at")[:6],
        },
    )


@login_required
def admin_user_list(request):
    require_admin(request)

    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "all")

    users = User.objects.filter(role=User.Role.STUDENT).annotate(
        folder_count=Count("research_folders", distinct=True),
        reference_count=Count("saved_references", distinct=True),
        note_count=Count("research_notes", distinct=True),
    )

    if query:
        users = users.filter(
            Q(full_name__icontains=query) | Q(email__icontains=query)
        )

    if status == "active":
        users = users.filter(is_active=True)
    elif status == "inactive":
        users = users.filter(is_active=False)

    return render(
        request,
        "study/admin/user_list.html",
        {
            "users": users.order_by("-created_at"),
            "query": query,
            "selected_status": status,
        },
    )


@login_required
def admin_user_detail(request, user_id):
    require_admin(request)

    student = get_object_or_404(
        User,
        id=user_id,
        role=User.Role.STUDENT,
    )

    return render(
        request,
        "study/admin/user_detail.html",
        {
            "student": student,
            "folders": student.research_folders.all()[:8],
            "references": student.saved_references.all()[:8],
            "notes": student.research_notes.select_related("folder").all()[:8],
            "deadlines": student.research_deadlines.select_related(
                "folder"
            ).all()[:8],
            "image_count": student.research_images.count(),
        },
    )


@login_required
@require_POST
def admin_user_toggle_active(request, user_id):
    require_admin(request)

    student = get_object_or_404(
        User,
        id=user_id,
        role=User.Role.STUDENT,
    )
    student.is_active = not student.is_active
    student.save(update_fields=["is_active", "updated_at"])

    action = "activated" if student.is_active else "deactivated"
    messages.success(request, f'"{student.full_name}" was {action}.')

    return redirect("admin_user_detail", user_id=student.id)


@login_required
def admin_content(request):
    require_admin(request)

    return render(
        request,
        "study/admin/content.html",
        {
            "folders": ResearchFolder.objects.select_related("owner")[:10],
            "references": SavedReference.objects.select_related("owner")[:10],
            "notes": ResearchNote.objects.select_related("owner", "folder")[:10],
            "deadlines": ResearchDeadline.objects.select_related(
                "owner", "folder"
            )[:10],
            "images": ResearchImage.objects.select_related("owner", "folder")[:10],
        },
    )
