# admissions/forms.py
from __future__ import annotations   # must be the first import

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import SportsQuotaApplication, ApplicationDocument, ApplicationCycle


class StartAdmissionForm(forms.Form):
    name = forms.CharField(
        label=_("Cycle name"),
        max_length=120,
        help_text=_("Example: 2025-26 UG"),
    )
    start_date = forms.DateField(label=_("Start date"), widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(label=_("End date"), widget=forms.DateInput(attrs={"type": "date"}))

    def clean(self):
        cleaned = super().clean()
        s = cleaned.get("start_date")
        e = cleaned.get("end_date")
        if s and e and s > e:
            self.add_error("end_date", _("End date must be on or after start date."))
        return cleaned


class ExtendAdmissionForm(forms.Form):
    cycle = forms.ModelChoiceField(
        queryset=ApplicationCycle.objects.all(),
        label=_("Cycle"),
        help_text=_("Pick the cycle to extend."),
    )
    new_end_date = forms.DateField(
        label=_("New end date"),
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text=_("Must be after the current end date."),
    )

    def clean(self):
        cleaned = super().clean()
        cycle: ApplicationCycle = cleaned.get("cycle")
        new_end = cleaned.get("new_end_date")
        if cycle and new_end and new_end <= cycle.end_date:
            self.add_error("new_end_date", _("New end date must be after current end date."))
        return cleaned


class StopAdmissionForm(forms.Form):
    cycle = forms.ModelChoiceField(
        queryset=ApplicationCycle.objects.filter(is_active=True),
        label=_("Active cycle"),
        help_text=_("Pick the active cycle to stop."),
    )


class SportsQuotaApplicationForm(forms.ModelForm):
    """
    Public-facing application form used by players/students.
    We deliberately do NOT expose 'status', 'reviewer', 'locked'.
    """
    class Meta:
        model = SportsQuotaApplication
        fields = [
            "cycle",
            "sport",
            "playing_position",
            "level",
            "years_experience",
            "previous_institution",
            "academic_summary",
            "achievements",
        ]
        widgets = {
            "achievements": forms.Textarea(attrs={"rows": 4}),
            "academic_summary": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("years_experience", 0) > 40:
            self.add_error("years_experience", _("Be serious."))
        return cleaned


class ApplicationDocumentForm(forms.ModelForm):
    """
    Separate form for each document so the UI can let users add multiple files.
    """
    class Meta:
        model = ApplicationDocument
        fields = ["doc_type", "file"]
