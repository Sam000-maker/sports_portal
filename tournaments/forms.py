from __future__ import annotations

from django import forms
from django.apps import apps
from django.contrib.auth import get_user_model

from .models import Tournament, TournamentTeam, Match, Lineup, LineupEntry
from players.models import Position  # assuming Position still lives here

User = get_user_model()


def _bs(field_or_bf, *, sel: bool = False, chk: bool = False, file: bool = False) -> None:
    """
    Apply Bootstrap classes safely whether you pass a Field or a BoundField.
    """
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
    Try to resolve eligible users for a team across the most likely schemas:
    1) players.TeamMembership (FK user, FK team, bool is_approved)
    2) team.members (M2M to user)
    3) team.players (M2M to user)
    4) fallback: all active users (last resort so the UI keeps working)
    """
    # 1) Through model path
    try:
        TeamMembership = apps.get_model("players", "TeamMembership")
    except LookupError:
        TeamMembership = None

    if TeamMembership is not None:
        qs_ids = TeamMembership.objects.filter(team=team)
        # Only apply 'is_approved' if field exists in your model
        if "is_approved" in {f.name for f in TeamMembership._meta.get_fields()}:
            qs_ids = qs_ids.filter(is_approved=True)
        user_ids = qs_ids.values_list("user_id", flat=True)
        return User.objects.filter(id__in=user_ids, is_active=True).distinct()

    # 2) team.members or 3) team.players
    if hasattr(team, "members"):
        return team.members.filter(is_active=True).distinct()
    if hasattr(team, "players"):
        return team.players.filter(is_active=True).distinct()

    # 4) Fallback
    return User.objects.filter(is_active=True)


class TournamentCreateForm(forms.ModelForm):
    """
    Model has `ttype` (not `type`) and no `seeding_method`.
    """
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
        if s and e and e < s:
            raise forms.ValidationError("End date cannot be before start date.")
        return cleaned


class AddTeamsForm(forms.ModelForm):
    """
    Attach a team to a tournament with optional seeding.
    """
    class Meta:
        model = TournamentTeam
        fields = ["team", "seed"]

    def __init__(self, *args, tournament: Tournament | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        for bf in self.visible_fields():
            _bs(bf)

        if tournament is not None:
            # Only teams matching the tournament sport
            self.fields["team"].queryset = self.fields["team"].queryset.filter(
                sport=tournament.sport
            )

    def clean_seed(self):
        seed = self.cleaned_data.get("seed")
        if seed is not None and seed <= 0:
            raise forms.ValidationError("Seed must be a positive number.")
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


class LineupEntryForm(forms.ModelForm):
    class Meta:
        model = LineupEntry
        fields = ["user", "position", "is_bench"]

    def __init__(self, *args, lineup: Lineup | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        for bf in self.visible_fields():
            _bs(bf)

        if lineup:
            # Use resilient resolver to avoid FieldError hell
            self.fields["user"].queryset = _eligible_users_for_team(lineup.team)

            # Only positions of that sport (assumes Team has FK sport)
            self.fields["position"].queryset = Position.objects.filter(
                sport=lineup.team.sport
            )


class ResultForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ["result", "status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bs(self.fields["status"], sel=True)
        _bs(self.fields["result"])


# Backward-compat aliases so your existing views import OK
TournamentForm = TournamentCreateForm
TournamentTeamForm = AddTeamsForm

__all__ = [
    "TournamentCreateForm",
    "AddTeamsForm",
    "ScheduleForm",
    "LineupEntryForm",
    "ResultForm",
    # legacy names:
    "TournamentForm",
    "TournamentTeamForm",
]
