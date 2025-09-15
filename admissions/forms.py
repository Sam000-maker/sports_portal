from __future__ import annotations

from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from .models import (
    SportsQuotaApplication,
    ApplicationDocument,
    ApplicationCycle,
)

# ---------------------------------------------------------
# Bootstrap helper: attach appropriate control classes
# ---------------------------------------------------------
def _add_bs(field: forms.Field, *, kind: str | None = None) -> None:
    cls = field.widget.attrs.get("class", "")
    want = (
        "form-select" if kind == "select"
        else "form-check-input" if kind == "checkbox"
        else "form-control"
    )
    if want not in cls.split():
        field.widget.attrs["class"] = (cls + " " + want).strip()


# ---------------------------------------------------------
# Admin Cycle Forms
# ---------------------------------------------------------
class StartAdmissionForm(forms.Form):
    name = forms.CharField(
        label=_("Cycle name"),
        max_length=120,
        help_text=_("Example: 2025-26 UG"),
        widget=forms.TextInput(attrs={"placeholder": _("e.g. 2025-26 UG")}),
    )
    start_date = forms.DateField(
        label=_("Start date"),
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    end_date = forms.DateField(
        label=_("End date"),
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for n in ("name", "start_date", "end_date"):
            _add_bs(self.fields[n])

    def clean(self):
        cleaned = super().clean()
        s, e = cleaned.get("start_date"), cleaned.get("end_date")
        if s and e and s > e:
            self.add_error("end_date", _("End date must be on or after start date."))
        return cleaned


class ExtendAdmissionForm(forms.Form):
    cycle = forms.ModelChoiceField(
        queryset=ApplicationCycle.objects.all(),
        label=_("Cycle"),
        help_text=_("Pick the cycle to extend."),
        widget=forms.Select(),
    )
    new_end_date = forms.DateField(
        label=_("New end date"),
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text=_("Must be after the current end date."),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_bs(self.fields["cycle"], kind="select")
        _add_bs(self.fields["new_end_date"])

    def clean(self):
        cleaned = super().clean()
        cycle: ApplicationCycle | None = cleaned.get("cycle")
        new_end = cleaned.get("new_end_date")
        if cycle and new_end and new_end <= cycle.end_date:
            self.add_error("new_end_date", _("New end date must be after current end date."))
        return cleaned


class StopAdmissionForm(forms.Form):
    cycle = forms.ModelChoiceField(
        queryset=ApplicationCycle.objects.filter(is_active=True),
        label=_("Active cycle"),
        help_text=_("Pick the active cycle to stop."),
        widget=forms.Select(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_bs(self.fields["cycle"], kind="select")


# ---------------------------------------------------------
# Public Applicant Form + Documents
# ---------------------------------------------------------
class SportsQuotaApplicationForm(forms.ModelForm):
    """
    Merged, user-facing application form with applicant details and photo.
    """
    consent = forms.BooleanField(
        required=True,
        label=_("I confirm the above information is true and I consent to processing."),
        widget=forms.CheckboxInput(),
    )

    class Meta:
        model = SportsQuotaApplication
        fields = [
            # cycle/sport
            "cycle", "sport", "playing_position", "level", "years_experience",
            # applicant details
            "full_name", "date_of_birth", "email", "phone",
            "address_line1", "address_line2", "city", "state", "postal_code", "country",
            "profile_photo", "consent",
            # academics & achievements
            "previous_institution", "academic_summary", "achievements",
        ]
        widgets = {
            "cycle": forms.Select(),
            # sport is free-text unless you provide choices on the model
            "sport": forms.TextInput(attrs={"placeholder": _("e.g. Football / Basketball / Badminton")}),
            "level": forms.Select(),
            "years_experience": forms.NumberInput(attrs={"min": 0, "max": 40, "step": 1, "inputmode": "numeric"}),
            "playing_position": forms.TextInput(attrs={"placeholder": _("e.g. Striker / Point Guard")}),
            "full_name": forms.TextInput(attrs={"placeholder": _("Your full name as per records")}),
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "email": forms.EmailInput(),
            "phone": forms.TextInput(attrs={"inputmode": "tel", "placeholder": _("e.g. +91 98xxxxxxx")}),
            "address_line1": forms.TextInput(attrs={"placeholder": _("House/Street/Locality")}),
            "address_line2": forms.TextInput(attrs={"placeholder": _("Area / Landmark (optional)")}),
            "city": forms.TextInput(),
            "state": forms.TextInput(),
            "postal_code": forms.TextInput(),
            "country": forms.TextInput(),
            "profile_photo": forms.ClearableFileInput(attrs={"accept": "image/*"}),
            "previous_institution": forms.TextInput(),
            "academic_summary": forms.Textarea(attrs={"rows": 3}),
            "achievements": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("cycle", "level"):
            _add_bs(self.fields[name], kind="select")
        for name, field in self.fields.items():
            if name == "consent":
                _add_bs(field, kind="checkbox")
            elif name not in ("cycle", "level"):
                _add_bs(field)

    def clean(self):
        cleaned = super().clean()
        years = cleaned.get("years_experience")
        if years is not None and years > 40:
            self.add_error("years_experience", _("Be realistic. 0–40 only."))
        return cleaned


class ApplicationDocumentForm(forms.ModelForm):
    class Meta:
        model = ApplicationDocument
        fields = ["doc_type", "file"]
        widgets = {
            "doc_type": forms.Select(),
            "file": forms.ClearableFileInput(attrs={"accept": ".pdf,image/*"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_bs(self.fields["doc_type"], kind="select")
        _add_bs(self.fields["file"])


ApplicationDocumentFormSet = inlineformset_factory(
    parent_model=SportsQuotaApplication,
    model=ApplicationDocument,
    form=ApplicationDocumentForm,
    extra=3,           # show 3 empty rows by default
    can_delete=True,   # allow removing rows before submit
    min_num=1,         # at least one document required
    validate_min=True,
)


# ---------------------------------------------------------
# Admin Edit Form (combined applicant + admin fields)
# ---------------------------------------------------------
class SportsQuotaAdminForm(forms.ModelForm):
    """
    Admin can edit applicant details and the review state in one place.
    We exclude 'consent' because admins aren’t applicants, and we add admin-only fields.
    """
    class Meta:
        model = SportsQuotaApplication
        fields = [
            # applicant-editable fields
            "cycle", "sport", "playing_position", "level", "years_experience",
            "full_name", "date_of_birth", "email", "phone",
            "address_line1", "address_line2", "city", "state", "postal_code", "country",
            "profile_photo", "previous_institution", "academic_summary", "achievements",
            # admin-only fields
            "status", "review_notes", "locked",
        ]
        widgets = {
            "cycle": forms.Select(),
            "sport": forms.TextInput(attrs={"placeholder": _("e.g. Football / Basketball / Badminton")}),
            "level": forms.Select(),
            "years_experience": forms.NumberInput(attrs={"min": 0, "max": 40, "step": 1, "inputmode": "numeric"}),
            "playing_position": forms.TextInput(attrs={"placeholder": _("e.g. Striker / Point Guard")}),
            "full_name": forms.TextInput(),
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "email": forms.EmailInput(),
            "phone": forms.TextInput(attrs={"inputmode": "tel"}),
            "address_line1": forms.TextInput(),
            "address_line2": forms.TextInput(),
            "city": forms.TextInput(),
            "state": forms.TextInput(),
            "postal_code": forms.TextInput(),
            "country": forms.TextInput(),
            "profile_photo": forms.ClearableFileInput(attrs={"accept": "image/*"}),
            "previous_institution": forms.TextInput(),
            "academic_summary": forms.Textarea(attrs={"rows": 3}),
            "achievements": forms.Textarea(attrs={"rows": 4}),
            "status": forms.Select(),
            "review_notes": forms.Textarea(attrs={"rows": 5, "placeholder": _("Optional notes for the review log")}),
            "locked": forms.CheckboxInput(),
        }
        help_texts = {
            "locked": _("Locked applications cannot be edited by the applicant."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("cycle", "level", "status"):
            _add_bs(self.fields[name], kind="select")
        _add_bs(self.fields["locked"], kind="checkbox")
        _add_bs(self.fields["review_notes"])
        # Everything else gets the default control class
        for name, field in self.fields.items():
            if name in {"cycle", "level", "status", "locked", "review_notes"}:
                continue
            _add_bs(field)

    def clean(self):
        cleaned = super().clean()
        years = cleaned.get("years_experience")
        if years is not None and years > 40:
            self.add_error("years_experience", _("Be realistic. 0–40 only."))
        return cleaned
