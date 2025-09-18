# accounts/views.py
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_protect
from django.urls import NoReverseMatch  # for safe fallbacks
from .models import Sport
from .forms import RegisterForm, LoginForm, ProfileForm, PendingPlayerRequestForm
from .models import PendingPlayerRequest

User = get_user_model()

# Simple cache-based rate limiter for login attempts
ATTEMPTS = getattr(settings, "LOGIN_RATE_LIMIT_ATTEMPTS", 5)
LOCKOUT_MIN = getattr(settings, "LOGIN_RATE_LIMIT_LOCKOUT_MINUTES", 10)

def _client_ip(request):
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

            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)

            Roles = getattr(user, "Roles", None)
            student_val = getattr(Roles, "STUDENT", "student")
            if getattr(user, "role", "") == student_val:
                try:
                    return redirect("players:dashboard")
                except NoReverseMatch:
                    return redirect("home")

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
    if request.method == "POST":
        logout(request)
        messages.info(request, "You have been logged out.")
        return redirect("home")
    return render(request, "accounts/logout_confirm.html")


@login_required
@csrf_protect
def profile_view(request):
    user = request.user
    profile_form = ProfileForm(request.POST or None, files=request.FILES or None, instance=user)

    request_form = PendingPlayerRequestForm(
        request.POST or None,
        user=user,
        prefix="req"
    )

    if request.method == "POST":
        actions = request.POST.getlist("action")
        action = actions[-1] if actions else None

        if action == "remove_avatar":
            if user.avatar:
                user.avatar.delete(save=False)
            user.avatar = None
            user.save(update_fields=["avatar"])
            messages.success(request, "Profile photo removed.")
            return redirect("accounts:profile")

        if action == "save_profile":
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profile updated.")
                return redirect("accounts:profile")

        if action == "become_player":
            if request_form.is_valid():
                with transaction.atomic():
                    request_form.save()
                messages.success(request, "Request submitted. An admin or coach will review it.")
                return redirect("accounts:profile")

    my_reqs = list(user.player_requests.all()[:5])

    has_pending = any(getattr(r, "status", "").lower() == "pending" for r in my_reqs)
    is_student = (getattr(user, "role", "") or "").lower() == "student"
    can_submit = (not is_student) and (not has_pending)

    return render(
        request,
        "accounts/profile.html",
        {
            "form": profile_form,
            "request_form": request_form,
            "my_requests": my_reqs,
            "user_sports": user.sports.all(),
            "can_submit_player_request": can_submit,  # << pass to template
        },
    )


@login_required
@csrf_protect
def delete_account_view(request):
    """
    True delete. Blocks deleting the last active superuser because you like disasters but not that much.
    """
    if request.method == "POST":
        u = request.user
        if u.is_superuser and User.objects.filter(is_superuser=True, is_active=True).count() <= 1:
            messages.error(request, "You can’t delete the last active superuser.")
            return redirect("accounts:profile")
        logout(request)
        u.delete()
        messages.info(request, "Your account has been deleted.")
        return redirect("home")

    return render(request, "accounts/delete_account_confirm.html")
