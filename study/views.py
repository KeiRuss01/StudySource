from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST

from .forms import EmailAuthenticationForm, SignUpForm
from .models import User


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
                "Your account was created successfully. Please log in.",
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

        next_url = request.POST.get("next") or request.GET.get("next")

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

    context = {
        "folder_count": 0,
        "reference_count": 0,
        "note_count": 0,
        "upcoming_deadline_count": 0,
    }

    return render(
        request,
        "study/dashboard.html",
        context,
    )


@require_POST
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("home")