from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone

from accounts.models import User
from .permissions import is_admin_like

admin_required = user_passes_test(is_admin_like, login_url="accounts:login")


@login_required
@admin_required
def dashboard(request):
    now = timezone.now()
    total_users = User.objects.count()
    by_role = (
        User.objects.values("role")
        .annotate(total=Count("id"))
        .order_by("role")
    )

    context = {
        "now": now,
        "total_users": total_users,
        "by_role": by_role,
        "kpi": {"active_tournaments": 0, "pending_bookings": 0, "pending_admissions": 0},
    }
    return render(request, "backoffice/dashboard.html", context)


@login_required
@admin_required
def users_list(request):
    """
    Users list with search + inline role dropdown support.
    """
    q = request.GET.get("q", "").strip()

    qs = User.objects.all().order_by("username")
    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q))

    page = Paginator(qs, 20).get_page(request.GET.get("page"))

    # Choices for the inline role dropdown
    roles_choices = list(User.Roles.choices)

    # Optional: hide "Admin" from non-admins so interns don't crown each other
    if not (request.user.is_superuser or getattr(request.user, "role", "") == User.Roles.ADMIN):
        roles_choices = [(v, l) for v, l in roles_choices if v != User.Roles.ADMIN]

    return render(
        request,
        "backoffice/users_list.html",
        {
            "page": page,
            "q": q,
            "roles_choices": roles_choices,  # <-- this feeds the dropdown
        },
    )
