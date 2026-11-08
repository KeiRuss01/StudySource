from django.urls import path

from . import note_views
from . import admin_views
from . import deadline_views
from . import image_views
from . import reference_views
from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),

    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path(
        "admin-dashboard/",
        admin_views.admin_dashboard,
        name="admin_dashboard",
    ),
    path(
        "admin-dashboard/users/",
        admin_views.admin_user_list,
        name="admin_user_list",
    ),
    path(
        "admin-dashboard/users/<int:user_id>/",
        admin_views.admin_user_detail,
        name="admin_user_detail",
    ),
    path(
        "admin-dashboard/users/<int:user_id>/toggle-active/",
        admin_views.admin_user_toggle_active,
        name="admin_user_toggle_active",
    ),
    path(
        "admin-dashboard/content/",
        admin_views.admin_content,
        name="admin_content",
    ),

    path(
        "dashboard/",
        views.student_dashboard,
        name="student_dashboard",
    ),

    path(
        "folders/",
        views.folder_list,
        name="folder_list",
    ),
    path(
        "folders/create/",
        views.folder_create,
        name="folder_create",
    ),
    path(
        "folders/<int:folder_id>/",
        views.folder_detail,
        name="folder_detail",
    ),
    path(
        "folders/<int:folder_id>/edit/",
        views.folder_update,
        name="folder_update",
    ),
    path(
        "folders/<int:folder_id>/delete/",
        views.folder_delete,
        name="folder_delete",
    ),

    path(
        "references/papers/",
        views.paper_search,
        name="paper_search",
    ),
    path(
        "references/papers/save/",
        views.save_openalex_reference,
        name="save_openalex_reference",
    ),
    path(
        "references/books/",
        reference_views.book_search,
        name="book_search",
    ),
    path(
        "references/doi/",
        reference_views.doi_lookup,
        name="doi_lookup",
    ),
    path(
        "references/external/save/",
        reference_views.save_external_reference,
        name="save_external_reference",
    ),
    path(
        "references/saved/",
        views.saved_reference_list,
        name="saved_reference_list",
    ),

    path(
        "notes/",
        note_views.note_list,
        name="note_list",
    ),
    path(
        "folders/<int:folder_id>/notes/create/",
        note_views.note_create,
        name="note_create",
    ),
    path(
        "notes/<int:note_id>/",
        note_views.note_detail,
        name="note_detail",
    ),
    path(
        "notes/<int:note_id>/edit/",
        note_views.note_update,
        name="note_update",
    ),
    path(
        "notes/<int:note_id>/delete/",
        note_views.note_delete,
        name="note_delete",
    ),

    path(
        "deadlines/",
        deadline_views.deadline_list,
        name="deadline_list",
    ),
    path("deadlines/calendar/connect/", deadline_views.calendar_connect, name="calendar_connect"),
    path("deadlines/calendar/callback/", deadline_views.calendar_callback, name="calendar_callback"),
    path("deadlines/calendar/disconnect/", deadline_views.calendar_disconnect, name="calendar_disconnect"),
    path(
        "deadlines/create/",
        deadline_views.deadline_create,
        name="deadline_create",
    ),
    path(
        "folders/<int:folder_id>/deadlines/create/",
        deadline_views.deadline_create,
        name="folder_deadline_create",
    ),
    path(
        "deadlines/<int:deadline_id>/edit/",
        deadline_views.deadline_update,
        name="deadline_update",
    ),
    path("deadlines/<int:deadline_id>/sync/", deadline_views.deadline_sync, name="deadline_sync"),
    path("deadlines/<int:deadline_id>/status/", deadline_views.deadline_status, name="deadline_status"),
    path(
        "deadlines/<int:deadline_id>/delete/",
        deadline_views.deadline_delete,
        name="deadline_delete",
    ),
    path(
        "folders/<int:folder_id>/images/upload/",
        image_views.image_upload,
        name="image_upload",
    ),
    path(
        "images/<int:image_id>/delete/",
        image_views.image_delete,
        name="image_delete",
    ),
]
