# facilities/forms.py
from __future__ import annotations

from django import forms
from .models import Venue, VenuePhoto, Booking


def _bs(field_or_bf, *, sel: bool = False, file: bool = False) -> None:
    """
    Bootstrap helper that works with either a Field or a BoundField.
    - sel: use form-select for <select>/<select multiple>
    - file: ensure form-control for file inputs
    """
    field = getattr(field_or_bf, "field", field_or_bf)  # BoundField -> Field
    widget = field.widget

    classes = widget.attrs.get("class", "").split()
    wanted = "form-select" if sel else "form-control"
    if file:
        wanted = "form-control"  # BS5 uses form-control for file inputs

    if wanted not in classes:
        classes.append(wanted)
    widget.attrs["class"] = " ".join(c for c in classes if c)


class VenueForm(forms.ModelForm):
    class Meta:
        model = Venue
        fields = ["name", "venue_type", "capacity", "location_note"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for bf in self.visible_fields():  # bf = BoundField
            _bs(bf, sel=isinstance(bf.field.widget, (forms.Select, forms.SelectMultiple)))


class VenuePhotoForm(forms.ModelForm):
    class Meta:
        model = VenuePhoto
        fields = ["image", "caption"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for bf in self.visible_fields():
            _bs(
                bf,
                sel=isinstance(bf.field.widget, (forms.Select, forms.SelectMultiple)),
                file=isinstance(bf.field.widget, forms.FileInput),
            )


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["venue", "start", "end", "purpose"]
        widgets = {
            "start": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for bf in self.visible_fields():
            _bs(bf, sel=isinstance(bf.field.widget, (forms.Select, forms.SelectMultiple)))

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start")
        end = cleaned.get("end")
        if start and end and end <= start:
            raise forms.ValidationError("End time must be after start time.")
        return cleaned
