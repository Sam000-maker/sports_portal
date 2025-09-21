from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models import Q, Count, Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, TemplateView, DeleteView

from .models import Team, TeamMembership, PositionGroup, Position, Formation, FormationPosition
from .forms import (
    TeamCreateForm,
    TeamInviteForm,
    MembershipUpdateForm,
    PositionGroupForm,
    PositionForm,
    FormationForm,
    FormationPositionFormSet,
)

User = get_user_model()


def is_admin_like(user) -> bool:
    return bool(
        getattr(user, "is_staff", False)
        or getattr(user, "role", "") in {"admin", "staff", "coach"}
    )


class StudentRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and getattr(
            self.request.user, "role", ""
        ) in {"student", "coach", "admin", "staff"}

    def handle_no_permission(self):
        messages.error(self.request, "Only logged-in students/coaches can access this page.")
        return redirect("accounts:profile")


# ---------------- Team screens ----------------
class TeamListView(StudentRequiredMixin, ListView):
    template_name = "players/team_list.html"
    context_object_name = "teams"

    def get_queryset(self):
        user = self.request.user
        return (
            Team.objects.filter(
                Q(created_by=user)
                | Q(memberships__user=user, memberships__status="active")
            )
            .annotate(
                approved_count=Count(
                    "memberships",
                    filter=Q(memberships__status="active"),
                    distinct=True,
                )
            )
            .select_related("sport", "created_by", "coach", "captain")
            .distinct()
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["pending_invites"] = (
            TeamMembership.objects.filter(user=self.request.user, status="pending")
            .select_related("team", "team__sport")
        )
        return ctx


class TeamCreateView(StudentRequiredMixin, CreateView):
    model = Team
    form_class = TeamCreateForm
    template_name = "players/team_form.html"

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["user"] = self.request.user
        return kw

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        resp = super().form_valid(form)
        TeamMembership.objects.get_or_create(
            team=self.object,
            user=self.request.user,
            defaults={"role": TeamMembership.Role.CAPTAIN, "status": "active"},
        )
        if not self.object.captain:
            self.object.captain = self.request.user
            self.object.save(update_fields=["captain"])
        messages.success(self.request, f"Team “{self.object.name}” created.")
        return resp

    def get_success_url(self):
        return reverse("players:team_detail", args=[self.object.pk])


class TeamDetailView(StudentRequiredMixin, TemplateView):
    template_name = "players/team_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        team = get_object_or_404(
            Team.objects.select_related("sport", "coach", "captain", "created_by"),
            pk=kwargs["pk"],
        )
        members = (
            TeamMembership.objects.filter(team=team, status="active")
            .select_related("user", "primary_position", "secondary_position")
            .order_by("jersey_no", "user__first_name")
        )
        pending = TeamMembership.objects.filter(team=team, status="pending").select_related("user")

        can_manage = (
            self.request.user == team.created_by
            or self.request.user == team.captain
            or is_admin_like(self.request.user)
        )
        invite_form = TeamInviteForm(team=team) if can_manage else None

        ctx.update(
            {"team": team, "members": members, "pending": pending, "invite_form": invite_form, "can_manage": can_manage}
        )
        return ctx

    def post(self, request, pk):
        team = get_object_or_404(Team, pk=pk)
        can_manage = (
            request.user == team.created_by
            or request.user == team.captain
            or is_admin_like(request.user)
        )
        if not can_manage:
            messages.error(request, "You don't have permission to invite.")
            return redirect("players:team_detail", pk=pk)

        form = TeamInviteForm(request.POST, team=team)
        if form.is_valid():
            invited = form.cleaned_data["user"]
            TeamMembership.objects.get_or_create(
                team=team, user=invited, defaults={"status": "pending"}
            )
            messages.success(request, f"Invitation sent to {invited}.")
            return redirect("players:team_detail", pk=pk)

        members = TeamMembership.objects.filter(team=team, status="active").select_related("user")
        pending = TeamMembership.objects.filter(team=team, status="pending").select_related("user")
        return render(
            request,
            self.template_name,
            {"team": team, "members": members, "pending": pending, "invite_form": form, "can_manage": can_manage},
        )


class AcceptInviteView(StudentRequiredMixin, View):
    def post(self, request, pk):
        team = get_object_or_404(Team, pk=pk)
        membership = get_object_or_404(TeamMembership, team=team, user=request.user)
        if membership.status == "pending":
            membership.status = "active"
            membership.save(update_fields=["status"])
            messages.success(request, f"You have joined {team.name}.")
        return redirect("players:team_detail", pk=pk)


class MembershipEditView(StudentRequiredMixin, UpdateView):
    model = TeamMembership
    form_class = MembershipUpdateForm
    template_name = "players/membership_form.html"

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["team"] = self.get_object().team
        return kw

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        can_manage = (
            request.user == obj.team.captain
            or request.user == obj.team.created_by
            or is_admin_like(request.user)
        )
        if not can_manage:
            messages.error(request, "You cannot edit this membership.")
            return redirect("players:team_detail", pk=obj.team_id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("players:team_detail", args=[self.object.team_id])


# -------------- Positions admin --------------
class PositionGroupCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = PositionGroup
    form_class = PositionGroupForm
    template_name = "players/position_group_form.html"
    success_url = reverse_lazy("players:position_admin")

    def test_func(self):
        return is_admin_like(self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["heading"] = "Position Group"
        return ctx


class PositionGroupUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = PositionGroup
    form_class = PositionGroupForm
    template_name = "players/position_group_form.html"
    success_url = reverse_lazy("players:position_admin")

    def test_func(self):
        return is_admin_like(self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["heading"] = "Position Group"
        return ctx


class PositionGroupDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = PositionGroup
    template_name = "players/confirm_delete.html"
    success_url = reverse_lazy("players:position_admin")

    def test_func(self):
        return is_admin_like(self.request.user)


class PositionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Position
    form_class = PositionForm
    template_name = "players/position_form.html"
    success_url = reverse_lazy("players:position_admin")

    def test_func(self):
        return is_admin_like(self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["heading"] = "Position"
        return ctx


class PositionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Position
    template_name = "players/confirm_delete.html"
    success_url = reverse_lazy("players:position_admin")

    def test_func(self):
        return is_admin_like(self.request.user)

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        # If position is used in a formation, PROTECT in model will raise; catch and message.
        try:
            resp = super().delete(request, *args, **kwargs)
            messages.success(request, f"Deleted position “{obj.name}”.")
            return resp
        except Exception:
            messages.error(request, "Cannot delete: position is used by one or more formations.")
            return redirect("players:position_admin")


# --------- Formation create/update/delete ----------
class FormationCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = "players/formation_form.html"

    def test_func(self):
        return is_admin_like(self.request.user)

    def get(self, request):
        form = FormationForm()
        formset = FormationPositionFormSet()
        return render(request, self.template_name, {"form": form, "formset": formset, "heading": "Formation"})

    @transaction.atomic
    def post(self, request):
        form = FormationForm(request.POST)
        if not form.is_valid():
            formset = FormationPositionFormSet(request.POST)
            return render(request, self.template_name, {"form": form, "formset": formset, "heading": "Formation"})

        formation = form.save(commit=False)
        # Build formset with sport-aware position queryset
        formset = FormationPositionFormSet(request.POST, instance=formation,
                                           form_kwargs={"sport": form.cleaned_data.get("sport")})
        if formset.is_valid():
            formation.save()
            formset.instance = formation
            formset.save()
            messages.success(request, f"Formation “{formation.name}” created.")
            return redirect("players:position_admin")

        return render(request, self.template_name, {"form": form, "formset": formset, "heading": "Formation"})


class FormationUpdateView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = "players/formation_form.html"

    def test_func(self):
        return is_admin_like(self.request.user)

    def get_object(self, pk) -> Formation:
        return get_object_or_404(Formation.objects.select_related("sport"), pk=pk)

    def get(self, request, pk):
        formation = self.get_object(pk)
        form = FormationForm(instance=formation)
        formset = FormationPositionFormSet(instance=formation, form_kwargs={"sport": formation.sport})
        return render(request, self.template_name, {"form": form, "formset": formset, "heading": "Formation", "object": formation})

    @transaction.atomic
    def post(self, request, pk):
        formation = self.get_object(pk)
        prev_sport = formation.sport_id
        form = FormationForm(request.POST, instance=formation)
        if not form.is_valid():
            formset = FormationPositionFormSet(request.POST, instance=formation, form_kwargs={"sport": formation.sport})
            return render(request, self.template_name, {"form": form, "formset": formset, "heading": "Formation", "object": formation})

        formation = form.save(commit=False)
        # If sport changed, we must ensure positions match new sport
        formset = FormationPositionFormSet(
            request.POST,
            instance=formation,
            form_kwargs={"sport": form.cleaned_data.get("sport")}
        )
        if formset.is_valid():
            formation.save()
            formset.save()
            if formation.sport_id != prev_sport:
                messages.info(request, "Sport changed; formation positions updated to match the new sport.")
            messages.success(request, f"Formation “{formation.name}” updated.")
            return redirect("players:position_admin")

        return render(request, self.template_name, {"form": form, "formset": formset, "heading": "Formation", "object": formation})


class FormationDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Formation
    template_name = "players/confirm_delete.html"
    success_url = reverse_lazy("players:position_admin")

    def test_func(self):
        return is_admin_like(self.request.user)


class PositionAdminDashboard(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "players/position_admin.html"

    def test_func(self):
        return is_admin_like(self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        groups = (
            PositionGroup.objects.select_related("sport")
            .prefetch_related("positions")
            .order_by("sport__code", "order")
        )
        formations = (
            Formation.objects.select_related("sport")
            .prefetch_related(
                Prefetch(
                    "positions",
                    queryset=FormationPosition.objects.select_related("position", "position__group"),
                )
            )
        )
        ctx["groups"] = groups
        ctx["positions"] = Position.objects.select_related("sport", "group")
        ctx["formations"] = formations
        return ctx
