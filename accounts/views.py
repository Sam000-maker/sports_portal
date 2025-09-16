# accounts/views.py
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import render, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_protect
from django.urls import NoReverseMatch  # for safe fallbacks

from .forms import RegisterForm, LoginForm, ProfileForm

# Simple cache-based rate limiter for login attempts
ATTEMPTS = getattr(settings, "LOGIN_RATE_LIMIT_ATTEMPTS", 5)
LOCKOUT_MIN = getattr(settings, "LOGIN_RATE_LIMIT_LOCKOUT_MINUTES", 10)


def _client_ip(request):
    # In production: use SECURE_PROXY_SSL_HEADER / X-Forwarded-For etc.
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


def _login_is_locked(request, username):
    ip = _client_ip(request)
    key = f"login:lock:{ip}:{username}"
    return cache.get(key) is not None


def _register_failed_attempt(request, username):
    ip = _client_ip(request)
    akey = f"login:attempts:{ip}:{username}"
    count = cache.get(akey, 0) + 1
    cache.set(akey, count, LOCKOUT_MIN * 60)
    if count >= ATTEMPTS:
        lkey = f"login:lock:{ip}:{username}"
        cache.set(lkey, True, LOCKOUT_MIN * 60)


def _reset_attempts(request, username):
    ip = _client_ip(request)
    cache.delete_many([f"login:attempts:{ip}:{username}", f"login:lock:{ip}:{username}"])


@csrf_protect
def register_view(request):
    """
    Handles user registration.
    """
    if request.method == "POST":
        form = RegisterForm(request.POST, files=request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful. You can log in now.")
            return redirect("accounts:login")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


@csrf_protect
def login_view(request):
    """
    Handles user login with simple rate-limiting.
    After login:
      - if ?next= is present and safe -> go there
      - elif role == STUDENT -> players:dashboard
      - else -> backoffice:dashboard, or home if that URL name doesn't exist
    """
    next_url = request.GET.get("next") or request.POST.get("next")

    if request.method == "POST":
        if _login_is_locked(request, request.POST.get("username", "")):
            messages.error(request, "Too many attempts. Try again later.")
            return render(request, "accounts/login.html", {"form": LoginForm(request), "next": next_url})

        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            _reset_attempts(request, request.POST.get("username", ""))
            login(request, user)
            messages.success(request, "Welcome back!")

            # 1) honor safe next URL if provided
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)

            # 2) role-based landing
            Roles = getattr(user, "Roles", None)
            student_val = getattr(Roles, "STUDENT", "student")
            if getattr(user, "role", "") == student_val:
                try:
                    return redirect("players:dashboard")
                except NoReverseMatch:
                    # if you forgot to include players.urls, fail gracefully
                    return redirect("home")

            # 3) fallback for staff/admin/others
            try:
                return redirect("backoffice:dashboard")
            except NoReverseMatch:
                return redirect("home")
        else:
            _register_failed_attempt(request, request.POST.get("username", ""))
    else:
        form = LoginForm(request)

    return render(request, "accounts/login.html", {"form": form, "next": next_url})


@login_required
@csrf_protect
def logout_view(request):
    """
    POST-only logout to avoid CSRF surprises.
    """
    if request.method == "POST":
        logout(request)
        messages.info(request, "You have been logged out.")
        return redirect("home")
    return render(request, "accounts/logout_confirm.html")


@login_required
@csrf_protect
def profile_view(request):
    user = request.user
    if request.method == "POST":
        form = ProfileForm(request.POST, files=request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=user)
    return render(request, "accounts/profile.html", {"form": form})
