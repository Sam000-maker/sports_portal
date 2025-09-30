# tournaments/forms.py
from __future__ import annotations

from typing import TypedDict

from django import forms
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Tournament, TournamentTeam, Match, Lineup, LineupEntry
from players.models import Position  # expected to have .code and optionally .sport

User = get_user_model()


def _bs(field_or_bf, *, sel: bool = False, chk: bool = False, file: bool = False) -> None:
    """Apply Bootstrap classes whether given a Field or a BoundField."""
    field = getattr(field_or_bf, "field", field_or_bf)
    widget = field.widget
    if not (sel or chk or file):
        sel = isinstance(widget, (forms.Select, forms.SelectMultiple))
        chk = isinstance(widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple))
        file = isinstance(widget, forms.ClearableFileInput)
    if chk:
        cls = "form-check-input"
    elif sel:
        cls = "form-select"
    else:
        cls = "form-control"
    widget.attrs["class"] = (widget.attrs.get("class", "") + " " + cls).strip()


def _eligible_users_for_team(team):
    """
    Resolve eligible users:
      1) players.TeamMembership (optional is_approved)
      2) team.members M2M
      3) team.players M2M
      4) fallback: all active users
    """
    try:
        TeamMembership = apps.get_model("players", "TeamMembership")
    except LookupError:
        TeamMembership = None

    if TeamMembership is not None:
        qs_ids = TeamMembership.objects.filter(team=team)
        if hasattr(TeamMembership, "is_approved"):
            qs_ids = qs_ids.filter(is_approved=True)
        user_ids = qs_ids.values_list("user_id", flat=True)
        return User.objects.filter(id__in=user_ids, is_active=True).distinct()

    if hasattr(team, "members"):
        return team.members.filter(is_active=True).distinct()
    if hasattr(team, "players"):
        return team.players.filter(is_active=True).distinct()

    return User.objects.filter(is_active=True)


class TournamentCreateForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = ["name", "sport", "ttype", "start_date", "end_date"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for bf in self.visible_fields():
            _bs(bf)

    def clean(self):
        cleaned = super().clean()
        s, e = cleaned.get("start_date"), cleaned.get("end_date")
        today = timezone.localdate()

        # New rule: start date cannot be in the past
        if s and s < today:
            raise ValidationError("Start date cannot be in the past.")

        # Existing rule: end must be >= start
        if s and e and e < s:
            raise ValidationError("End date cannot be before start date.")
        return cleaned


class AddTeamsForm(forms.ModelForm):
    class Meta:
        model = TournamentTeam
        fields = ["team", "seed"]

    def __init__(self, *args, tournament: Tournament | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        for bf in self.visible_fields():
            _bs(bf)
        if tournament is not None:
            self.fields["team"].queryset = self.fields["team"].queryset.filter(sport=tournament.sport)

    def clean_seed(self):
        seed = self.cleaned_data.get("seed")
        if seed is not None and seed <= 0:
            raise ValidationError("Seed must be a positive number.")
        return seed


class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ["scheduled_at", "venue", "officials"]
        widgets = {"scheduled_at": forms.DateTimeInput(attrs={"type": "datetime-local"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for bf in self.visible_fields():
            _bs(bf)

    def clean_scheduled_at(self):
        dt = self.cleaned_data.get("scheduled_at")
        if dt and timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        return dt


class ResultPayload(TypedDict, total=False):
    a: int        # score for team_a
    b: int        # score for team_b
    winner: int   # team id of winner
    note: str


class LineupEntryForm(forms.ModelForm):
    class Meta:
        model = LineupEntry
        fields = ["user", "position", "is_bench"]

    def __init__(self, *args, lineup: Lineup | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        for bf in self.visible_fields():
            _bs(bf)
        if lineup:
            self.fields["user"].queryset = _eligible_users_for_team(lineup.team)
            if hasattr(Position, "sport"):
                self.fields["position"].queryset = Position.objects.filter(sport=lineup.team.sport)


class ResultForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ["result", "status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bs(self.fields["status"], sel=True)
        _bs(self.fields["result"])

    def clean_result(self):
        data = self.cleaned_data.get("result")
        if data is None:
            return data
        for key in ("a", "b"):
            if key in data and not isinstance(data[key], int):
                raise ValidationError(f"Result[{key}] must be an integer score.")
        if "winner" in data and not isinstance(data["winner"], int):
            raise ValidationError("Result[winner] must be a team id (int).")
        return data


# Backward-compat aliases
TournamentForm = TournamentCreateForm
TournamentTeamForm = AddTeamsForm

__all__ = [
    "TournamentCreateForm",
    "AddTeamsForm",
    "ScheduleForm",
    "LineupEntryForm",
    "ResultForm",
    "TournamentForm",
    "TournamentTeamForm",
]
