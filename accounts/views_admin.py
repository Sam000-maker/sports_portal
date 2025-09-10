from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db import models
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import AdminRoleUpdateForm
from .models import RoleChangeLog
from .permissions import admin_required

User = get_user_model()


def _safe_redirect(request, fallback_name="accounts:users_list"):
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    try:
        return redirect(reverse(fallback_name))
    except Exception:
        return redirect("/")


@login_required
@admin_required()
def users_list(request):
    q = (request.GET.get("q") or "").strip()
    qs = User.objects.all().order_by("username")
    if q:
        qs = qs.filter(
            models.Q(username__icontains=q)
            | models.Q(email__icontains=q)
            | models.Q(first_name__icontains=q)
            | models.Q(last_name__icontains=q)
        )
    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "accounts/users_list.html", {"page": page, "q": q})


@login_required
@admin_required()
@transaction.atomic
def change_user_role(request, user_id):
    target = get_object_or_404(User, pk=user_id)

    def _count_superusers():
        return User.objects.filter(is_superuser=True, is_active=True).count()

    if request.method == "POST":
        form = AdminRoleUpdateForm(target_user=target, acting_user=request.user, data=request.POST)
        if form.is_valid():
            old_role = target.role
            new_role = form.cleaned_data["role"]

            if target.is_superuser and new_role != User.Roles.ADMIN and _count_superusers() == 1:
                messages.error(request, "You cannot change the role of the last superuser.")
                return _safe_redirect(request)

            target.role = new_role
            target.save(update_fields=["role"])

            RoleChangeLog.objects.create(
                target=target,
                changed_by=request.user,
                old_role=old_role,
                new_role=new_role,
                reason=form.cleaned_data.get("reason", "Inline change"),
            )

            messages.success(request, f"Role updated: {target.username} → {target.get_role_display()}.")
            return _safe_redirect(request, fallback_name="accounts:users_list")
        else:
            messages.error(request, "; ".join([" ".join(err_list) for err_list in form.errors.values()]) or "Invalid input.")
            return _safe_redirect(request)
    else:
        form = AdminRoleUpdateForm(target_user=target, acting_user=request.user, initial={"role": target.role})
        return render(request, "accounts/change_user_role.html", {"form": form, "target": target})
