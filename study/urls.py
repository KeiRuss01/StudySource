from django.urls import path

from . import views


urlpatterns = [
    path(
        "",
        views.home,
        name="home",
    ),
    path(
        "about/",
        views.about,
        name="about",
    ),
    path(
        "signup/",
        views.signup_view,
        name="signup",
    ),
    path(
        "login/",
        views.login_view,
        name="login",
    ),
    path(
        "logout/",
        views.logout_view,
        name="logout",
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
]