from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model
from django.forms import inlineformset_factory

from .models import (
    Team, TeamMembership, PositionGroup, Position,
    Formation, FormationPosition
)

User = get_user_model()


def _bs(field_or_bf, *, sel: bool = False, chk: bool = False, file: bool = False) -> None:
    """
    Apply correct Bootstrap 5 classes:
      - text inputs: form-control
      - selects: form-select
      - checkboxes: form-check-input
      - file inputs: form-control
    Also remove any conflicting class that would break rendering.
    """
    field = getattr(field_or_bf, "field", field_or_bf)  # BoundField -> Field
    widget = field.widget
    classes = set(widget.attrs.get("class", "").split())

    # Nuke wrong classes first
    classes.discard("form-control")
    classes.discard("form-select")
    classes.discard("form-check-input")

    if chk:
        classes.add("form-check-input")
    elif sel:
        classes.add("form-select")
    else:
        classes.add("form-control")

    widget.attrs["class"] = " ".join(sorted(c for c in classes if c))


class TeamCreateForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["sport", "name", "coach", "captain", "home_venues"]
        widgets = {"home_venues": forms.SelectMultiple(attrs={"size": 6})}

    def __init__(self, *args, user: User | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        for bf in self.visible_fields():
            _bs(
                bf,
                sel=isinstance(bf.field.widget, (forms.Select, forms.SelectMultiple)),
                chk=isinstance(bf.field.widget, forms.CheckboxInput),
                file=isinstance(bf.field.widget, forms.FileInput),
            )

        qs = User.objects.filter(is_active=True)
        if "coach" in self.fields:
            self.fields["coach"].queryset = qs
        if "captain" in self.fields:
            self.fields["captain"].queryset = qs

        if user and user.is_authenticated and "captain" in self.fields and not self.instance.pk:
            try:
                self.fields["captain"].initial = user.pk
            except Exception:
                pass

    def clean(self):
        cleaned = super().clean()
        sport = cleaned.get("sport")
        if not sport:
            raise forms.ValidationError("Pick a sport.")
        return cleaned


class TeamInviteForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.none(), label="Invite user")

    def __init__(self, *args, team: Team, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = (
            User.objects.filter(is_active=True)
            .exclude(team_memberships__team=team)
            .order_by("username")
        )
        _bs(self.fields["user"], sel=True)


class MembershipUpdateForm(forms.ModelForm):
    class Meta:
        model = TeamMembership
        fields = ["role", "status", "jersey_no", "primary_position", "secondary_position"]

    def __init__(self, *args, team: Team, **kwargs):
        super().__init__(*args, **kwargs)
        for bf in self.visible_fields():
            _bs(bf, sel=isinstance(bf.field.widget, forms.Select))

        self.fields["primary_position"].queryset = Position.objects.filter(sport=team.sport)
        self.fields["secondary_position"].queryset = Position.objects.filter(sport=team.sport)

    def clean_jersey_no(self):
        num = self.cleaned_data.get("jersey_no")
        if num is not None and num <= 0:
            raise forms.ValidationError("Jersey number must be a positive integer.")
        return num


class PositionGroupForm(forms.ModelForm):
    class Meta:
        model = PositionGroup
        fields = ["sport", "name", "order"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for bf in self.visible_fields():
            _bs(bf, sel=isinstance(bf.field.widget, forms.Select))


class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ["sport", "group", "name", "code", "min_per_lineup", "max_per_lineup", "is_unique"]
        widgets = {
            "is_unique": forms.CheckboxInput(),  # belt-and-suspenders
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for bf in self.visible_fields():
            _bs(
                bf,
                sel=isinstance(bf.field.widget, forms.Select),
                chk=isinstance(bf.field.widget, forms.CheckboxInput),
            )

    def clean(self):
        cleaned = super().clean()
        min_cnt = cleaned.get("min_per_lineup") or 0
        max_cnt = cleaned.get("max_per_lineup") or 0
        if max_cnt and min_cnt and max_cnt < min_cnt:
            raise forms.ValidationError("Max per lineup cannot be less than min per lineup.")
        return cleaned


class FormationForm(forms.ModelForm):
    class Meta:
        model = Formation
        fields = ["sport", "name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for bf in self.visible_fields():
            _bs(bf, sel=isinstance(bf.field.widget, forms.Select))


class _FormationPositionForm(forms.ModelForm):
    class Meta:
        model = FormationPosition
        fields = ["position", "count"]

    def __init__(self, *args, sport=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Restrict positions by sport if provided, otherwise leave empty to avoid cross-sport mess
        if sport is not None:
            self.fields["position"].queryset = Position.objects.filter(sport=sport).order_by("group__order", "name")
        for bf in self.visible_fields():
            _bs(bf, sel=isinstance(bf.field.widget, forms.Select))


FormationPositionFormSet = inlineformset_factory(
    parent_model=Formation,
    model=FormationPosition,
    form=_FormationPositionForm,
    fields=["position", "count"],
    extra=4,
    can_delete=True,
    min_num=0,
    validate_min=False,
)
