# tournaments/views.py
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import ListView, CreateView, DetailView, FormView, UpdateView

from .models import Tournament, TournamentTeam, Match, Lineup, LineupEntry
from .forms import TournamentForm, TournamentTeamForm, ScheduleForm, LineupEntryForm, ResultForm
from .services import generate_fixtures
from facilities.models import Booking


# --------- Role helpers ---------
def role_of(user) -> str:
    """Return simplified role string: admin|coach|student|other."""
    # You said you have user.role; we also treat staff as admin-like.
    if getattr(user, "is_staff", False) or getattr(user, "role", "") == "admin":
        return "admin"
    if getattr(user, "role", "") == "coach":
        return "coach"
    if getattr(user, "role", "") in {"student", "athlete"}:
        return "student"
    return "other"


def is_admin_like(user) -> bool:
    return role_of(user) == "admin" or getattr(user, "role", "") in {"staff"}


def is_coach(user) -> bool:
    return role_of(user) == "coach"


def is_student(user) -> bool:
    return role_of(user) == "student"


# --------- Permission Mixins ---------
class AdminRequired(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True
    def test_func(self):
        return is_admin_like(self.request.user)


class CoachRequired(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True
    def test_func(self):
        return is_coach(self.request.user) or is_admin_like(self.request.user)


class AdminCoachRequired(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True
    def test_func(self):
        return is_admin_like(self.request.user) or is_coach(self.request.user)


class StudentRequired(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True
    def test_func(self):
        return is_student(self.request.user)


# --------- Capability flags (for templates) ---------
def capability_map(user):
    r = role_of(user)
    return {
        "is_admin": r == "admin",
        "is_coach": r == "coach",
        "is_student": r == "student",
        # granular abilities
        "can_create": r in {"admin", "coach"},
        "can_edit_tournament": r in {"admin"},           # keep editing destructive to admin only
        "can_delete_tournament": r in {"admin"},         # admin-only destructive
        "can_add_team": r in {"admin", "coach"},
        "can_generate_fixtures": r in {"admin", "coach"},
        "can_schedule": r in {"admin", "coach"},
        "can_manage_lineups": r in {"admin", "coach"},
        "can_enter_results": r in {"admin", "coach"},
    }


# ---------------- Base/Shared ----------------
class BaseTournamentListView(LoginRequiredMixin, ListView):
    model = Tournament
    context_object_name = "tournaments"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        caps = capability_map(self.request.user)
        ctx.update(caps)
        return ctx


class BaseTournamentDetailView(LoginRequiredMixin, DetailView):
    model = Tournament
    context_object_name = "tournament"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        t = self.object
        caps = capability_map(self.request.user)
        ctx["teams"] = (
            TournamentTeam.objects.filter(tournament=t)
            .select_related("team", "team__sport")
            .order_by("seed", "team__name")
        )
        ctx["matches"] = (
            Match.objects.filter(tournament=t)
            .select_related("team_a", "team_b", "venue")
            .order_by("round_no", "group_label", "id")
        )
        if caps["can_add_team"]:
            ctx["form"] = TournamentTeamForm(tournament=t)
        ctx.update(caps)
        return ctx


# ---------------- Role-specific pages ----------------

# Admin pages
class TournamentListAdminView(AdminRequired, BaseTournamentListView):
    template_name = "tournaments/admin/tournament_list_admin.html"


class TournamentDetailAdminView(AdminRequired, BaseTournamentDetailView):
    template_name = "tournaments/admin/tournament_detail_admin.html"


# Coach pages
class TournamentListCoachView(CoachRequired, BaseTournamentListView):
    template_name = "tournaments/coach/tournament_list_coach.html"


class TournamentDetailCoachView(CoachRequired, BaseTournamentDetailView):
    template_name = "tournaments/coach/tournament_detail_coach.html"


# Student pages (read-only)
class TournamentListStudentView(StudentRequired, BaseTournamentListView):
    template_name = "tournaments/student/tournament_list_student.html"


class TournamentDetailStudentView(StudentRequired, BaseTournamentDetailView):
    template_name = "tournaments/student/tournament_detail_student.html"


# ---------------- Legacy “generic” routes (kept for compatibility) ----------------
class TournamentListView(LoginRequiredMixin, ListView):
    model = Tournament
    template_name = "tournaments/tournament_list.html"
    context_object_name = "tournaments"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(capability_map(self.request.user))
        return ctx


class TournamentCreateView(AdminCoachRequired, CreateView):
    model = Tournament
    form_class = TournamentForm
    template_name = "tournaments/tournament_form.html"
    success_url = reverse_lazy("tournaments:tournament_list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Tournament created. Add teams next.")
        return super().form_valid(form)


class TournamentUpdateView(AdminRequired, UpdateView):
    model = Tournament
    form_class = TournamentForm
    template_name = "tournaments/tournament_form.html"
    success_url = reverse_lazy("tournaments:tournament_list")

    def form_valid(self, form):
        messages.success(self.request, "Tournament updated successfully.")
        return super().form_valid(form)


@method_decorator(require_POST, name="dispatch")
class TournamentDeleteView(AdminRequired, View):
    def post(self, request, pk):
        t = get_object_or_404(Tournament, pk=pk)
        t.delete()
        messages.success(request, "Tournament deleted.")
        return redirect("tournaments:tournament_list")


class TournamentDetailView(LoginRequiredMixin, DetailView):
    model = Tournament
    template_name = "tournaments/tournament_detail.html"
    context_object_name = "tournament"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        t = self.object
        caps = capability_map(self.request.user)
        ctx["teams"] = (
            TournamentTeam.objects.filter(tournament=t)
            .select_related("team", "team__sport")
            .order_by("seed", "team__name")
        )
        ctx["matches"] = (
            Match.objects.filter(tournament=t)
            .select_related("team_a", "team_b", "venue")
            .order_by("round_no", "group_label", "id")
        )
        if caps["can_add_team"]:
            ctx["form"] = TournamentTeamForm(tournament=t)
        ctx.update(caps)
        return ctx


class TournamentTeamAddView(AdminCoachRequired, FormView):
    form_class = TournamentTeamForm
    template_name = "tournaments/tournament_team_form.html"

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["tournament"] = get_object_or_404(Tournament, pk=self.kwargs["pk"])
        return kw

    def form_valid(self, form):
        t = get_object_or_404(Tournament, pk=self.kwargs["pk"])
        tt = form.save(commit=False)
        tt.tournament = t
        tt.save()
        messages.success(self.request, "Team added.")
        return redirect("tournaments:tournament_detail", pk=t.pk)


@method_decorator(require_POST, name="dispatch")
class TournamentTeamRemoveView(AdminCoachRequired, View):
    def post(self, request, pk, tt_id):
        t = get_object_or_404(Tournament, pk=pk)
        tt = get_object_or_404(TournamentTeam, pk=tt_id, tournament=t)
        tt.delete()
        messages.success(self.request, "Team removed from tournament.")
        return redirect("tournaments:tournament_detail", pk=t.pk)


class TournamentGenerateFixturesView(AdminCoachRequired, View):
    def post(self, request, pk):
        t = get_object_or_404(Tournament, pk=pk)
        if TournamentTeam.objects.filter(tournament=t).count() < 2:
            messages.error(self.request, "You need at least 2 teams to generate fixtures.")
            return redirect("tournaments:tournament_detail", pk=pk)
        try:
            generate_fixtures(t)
        except Exception as e:
            messages.error(self.request, f"Could not generate fixtures: {e}")
        else:
            messages.success(self.request, "Fixtures generated.")
        return redirect("tournaments:tournament_detail", pk=pk)


# ------------- Scheduling & bookings -------------
class MatchScheduleView(AdminCoachRequired, FormView):
    form_class = ScheduleForm
    template_name = "tournaments/match_schedule_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.match = get_object_or_404(Match, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        m = self.match
        return {"scheduled_at": m.scheduled_at, "venue": m.venue, "officials": m.officials}

    def form_valid(self, form):
        m = self.match
        m.scheduled_at = form.cleaned_data["scheduled_at"]
        m.venue = form.cleaned_data["venue"]
        m.officials = form.cleaned_data["officials"]
        m.save()

        # Auto-create a facility booking for a 2-hour slot
        if m.venue and m.scheduled_at:
            from datetime import timedelta
            start = m.scheduled_at
            end = start + timedelta(hours=2)
            defaults = {"created_by": self.request.user, "purpose": f"Match {m.id}"}
            if hasattr(Booking, "tournament_match"):
                defaults["tournament_match"] = m
            Booking.objects.get_or_create(
                venue=m.venue,
                start=start,
                end=end,
                defaults=defaults,
            )
        messages.success(self.request, "Match scheduled and venue booked.")
        return redirect("tournaments:tournament_detail", pk=m.tournament_id)


# ---------------- Lineups & results ----------------
class LineupBuildView(AdminCoachRequired, FormView):
    template_name = "tournaments/lineup_form.html"
    form_class = LineupEntryForm

    def dispatch(self, request, *args, **kwargs):
        self.match = get_object_or_404(Match, pk=kwargs["match_id"])
        self.team_side = kwargs["side"]  # "a" or "b"
        if self.team_side not in {"a", "b"}:
            messages.error(self.request, "Invalid team side.")
            return redirect("tournaments:tournament_detail", pk=self.match.tournament_id)
        team = self.match.team_a if self.team_side == "a" else self.match.team_b
        self.lineup, _ = Lineup.objects.get_or_create(match=self.match, team=team)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["lineup"] = self.lineup
        return kw

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["match"] = self.match
        ctx["lineup"] = self.lineup
        ctx["team_side"] = self.team_side
        ctx["entries"] = (
            LineupEntry.objects.filter(lineup=self.lineup)
            .select_related("user", "position")
            .order_by("is_bench", "id")
        )
        return ctx

    def form_valid(self, form):
        entry = form.save(commit=False)
        entry.lineup = self.lineup
        try:
            with transaction.atomic():
                entry.save()
        except IntegrityError:
            messages.error(self.request, "That player is already in this lineup.")
        else:
            messages.success(self.request, "Player added to lineup.")
        return redirect("tournaments:tournament_detail", pk=self.match.tournament_id)


@method_decorator(require_POST, name="dispatch")
class LineupEntryRemoveView(AdminCoachRequired, View):
    def post(self, request, match_id, entry_id):
        match = get_object_or_404(Match, pk=match_id)
        entry = get_object_or_404(LineupEntry, pk=entry_id, lineup__match=match)
        entry.delete()
        messages.success(self.request, "Player removed from lineup.")
        return redirect("tournaments:tournament_detail", pk=match.tournament_id)


class ResultUpdateView(AdminCoachRequired, FormView):
    form_class = ResultForm
    template_name = "tournaments/result_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.match = get_object_or_404(Match, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        return {"result": self.match.result, "status": self.match.status}

    def form_valid(self, form):
        self.match.result = form.cleaned_data["result"]
        self.match.status = form.cleaned_data["status"]
        self.match.save(update_fields=["result", "status"])
        messages.success(self.request, "Result updated.")
        return redirect("tournaments:tournament_detail", pk=self.match.tournament_id)


@method_decorator(require_POST, name="dispatch")
class MatchDeleteView(AdminRequired, View):
    def post(self, request, pk):
        match = get_object_or_404(Match, pk=pk)
        tid = match.tournament_id
        match.delete()
        messages.success(self.request, "Match deleted.")
        return redirect("tournaments:tournament_detail", pk=tid)
