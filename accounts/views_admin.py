# accounts/views_admin.py
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.utils.http import url_has_allowed_host_and_scheme


from .models import PendingPlayerRequest, RoleChangeLog
from .permissions import admin_or_coach_required
from .forms import AdminRoleUpdateForm

User = get_user_model()

# ---------- Users list (admin/coach) ----------
@admin_or_coach_required
def users_list(request):
    # Filters
    q = (request.GET.get("q") or "").strip()
    role = request.GET.get("role") or ""
    staff = request.GET.get("staff") or ""   # '1' | '0' | ''
    active = request.GET.get("active") or "" # '1' | '0' | ''
    order = request.GET.get("order") or "username"

    allowed_orders = {"username", "-last_login", "last_login"}
    if order not in allowed_orders:
        order = "username"

    # Base queryset
    qs = User.objects.all()

    if q:
        qs = qs.filter(
            Q(username__icontains=q)
            | Q(email__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
        )
    if role:
        qs = qs.filter(role=role)
    if staff in {"1", "0"}:
        qs = qs.filter(is_staff=(staff == "1"))
    if active in {"1", "0"}:
        qs = qs.filter(is_active=(active == "1"))

    # Ordering
    if order == "username":
        qs = qs.order_by("username")
    else:
        qs = qs.order_by(order, "username")  # stable secondary key

    # KPI on filtered set
    filtered = qs
    kpi = {
        "total": filtered.count(),
        "active": filtered.filter(is_active=True).count(),
        "staff": filtered.filter(is_staff=True).count(),
        "superusers": filtered.filter(is_superuser=True).count(),
    }

    # Role summary on filtered set
    roles_summary = (
        filtered.values("role")
        .annotate(total=Count("id"))
        .order_by("role")
    )

    # Choices for inline role dropdown
    roles_choices = list(User.Roles.choices)

    # Pagination
    page = Paginator(qs, 25).get_page(request.GET.get("page"))

    # Echo filters for template
    filters = {"q": q, "role": role, "staff": staff, "active": active, "order": order}

    return render(
        request,
        "accounts/admin_users_list.html",
        {
            "page": page,
            "kpi": kpi,
            "filters": filters,
            "roles_choices": roles_choices,
            "roles_summary": roles_summary,
        },
    )


# ---------- Change a user's role (admin/coach) ----------
@admin_or_coach_required
@require_http_methods(["GET", "POST"])
def change_user_role(request, user_id):
    target = get_object_or_404(User, pk=user_id)

    if request.method == "POST":
        form = AdminRoleUpdateForm(target_user=target, acting_user=request.user, data=request.POST)
        if form.is_valid():
            new_role = form.cleaned_data["role"]
            reason = form.cleaned_data.get("reason", "")

            with transaction.atomic():
                old_role = target.role
                target.role = new_role
                target.save(update_fields=["role"])
                RoleChangeLog.objects.create(
                    target=target,
                    changed_by=request.user,
                    old_role=old_role,
                    new_role=new_role,
                    reason=reason or "Role changed via backoffice",
                )

            # Respect ?next so the inline dropdown returns to the same filter/page
            next_url = request.POST.get("next")
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)

            messages.success(request, f"Updated {target.username} to {new_role}.")
            return redirect("accounts:users_list")
    else:
        form = AdminRoleUpdateForm(target_user=target, acting_user=request.user)

    return render(request, "accounts/change_user_role.html", {"form": form, "target": target})


# ---------- Player requests review (admin/coach) ----------
@admin_or_coach_required
def player_requests_list(request):
    # Filters
    q = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "pending").lower()
    order = request.GET.get("order") or "-submitted_at"
    allowed_orders = {"-submitted_at", "submitted_at", "-id", "id"}
    if order not in allowed_orders:
        order = "-submitted_at"

    # Base queryset for search-only (for KPI/summary across all statuses)
    base = PendingPlayerRequest.objects.select_related("user").prefetch_related("sports")
    if q:
        base = base.filter(Q(user__username__icontains=q) | Q(user__email__icontains=q))

    # Summary by status on the search-filtered set
    summary = dict(
        (row["status"], row["total"])
        for row in base.values("status").annotate(total=Count("id"))
    )
    # Ensure keys exist
    for s in ("pending", "approved", "rejected"):
        summary.setdefault(s, 0)

    # KPI on the search-filtered set
    kpi = {
        "total": base.count(),
        "pending": summary["pending"],
        "approved": summary["approved"],
        "rejected": summary["rejected"],
    }

    # Apply status + ordering for the page list
    qs = base
    if status in {"pending", "approved", "rejected"}:
        qs = qs.filter(status=status)
    qs = qs.order_by(order, "-id")  # stable secondary key

    # Pagination
    page = Paginator(qs, 25).get_page(request.GET.get("page"))

    filters = {"q": q, "status": status, "order": order}

    return render(
        request,
        "accounts/player_requests_list.html",
        {
            "page": page,
            "kpi": kpi,
            "filters": filters,
            "status_summary": [
                {"status": "pending", "total": summary["pending"]},
                {"status": "approved", "total": summary["approved"]},
                {"status": "rejected", "total": summary["rejected"]},
            ],
            # legacy var name some snippets still reference
            "filter_status": status,
        },
    )

@admin_or_coach_required
@require_http_methods(["POST"])
def review_player_request(request, pk, action):
    req = get_object_or_404(PendingPlayerRequest, pk=pk)

    if req.status != PendingPlayerRequest.Status.PENDING:
        messages.info(request, "Request already reviewed.")
        return redirect("accounts:player_requests_list")

    if action not in {"approve", "reject"}:
        messages.error(request, "Unknown action.")
        return redirect("accounts:player_requests_list")

    with transaction.atomic():
        req.reviewed_by = request.user
        req.reviewed_at = timezone.now()

        if action == "reject":
            req.status = PendingPlayerRequest.Status.REJECTED
            req.review_note = "Rejected"
            req.save()
            messages.info(request, "Request rejected.")
            return redirect("accounts:player_requests_list")

        # Approve
        req.status = PendingPlayerRequest.Status.APPROVED
        req.review_note = "Approved"
        req.save()

        u = req.user
        old_role = u.role
        u.role = User.Roles.STUDENT
        u.save(update_fields=["role"])
        u.sports.set(req.sports.all())

        RoleChangeLog.objects.create(
            target=u, changed_by=request.user, old_role=old_role, new_role=u.role, reason="Approved player request"
        )
        messages.success(request, f"Approved {u.username} and promoted to Student.")
        return redirect("accounts:player_requests_list")
