from __future__ import annotations

from datetime import timedelta

from django import forms
from django.db.models import Q, Sum, F, ExpressionWrapper, DurationField, Value
from django.utils.timezone import localdate

from .models import Venue, VenuePhoto, Booking


def _bs(field_or_bf, *, sel: bool = False, file: bool = False) -> None:
    field = getattr(field_or_bf, "field", field_or_bf)
    widget = field.widget
    classes = widget.attrs.get("class", "").split()
    wanted = "form-select" if sel else "form-control"
    if file:
        wanted = "form-control"
    if wanted not in classes:
        classes.append(wanted)
    widget.attrs["class"] = " ".join(c for c in classes if c)


class VenueForm(forms.ModelForm):
    class Meta:
        model = Venue
        fields = ["name", "venue_type", "capacity", "location_note", "is_active"]  # include active toggle in admin form

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for bf in self.visible_fields():
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
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self._user = user  # used for daily cap
        # Only allow booking into active venues, but keep current instance venue selectable for edits
        qs = Venue.objects.filter(is_active=True)
        if self.instance and self.instance.pk and self.instance.venue_id:
            qs = Venue.objects.filter(Q(pk=self.instance.venue_id) | Q(is_active=True))
        self.fields["venue"].queryset = qs.order_by("name")
        for bf in self.visible_fields():
            _bs(bf, sel=isinstance(bf.field.widget, (forms.Select, forms.SelectMultiple)))

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start")
        end = cleaned.get("end")
        venue = cleaned.get("venue")

        # Basic chronological check
        if start and end and end <= start:
            raise forms.ValidationError("End time must be after start time.")

        # Same-day policy to keep daily-cap simple
        if start and end and start.date() != end.date():
            raise forms.ValidationError("Bookings must start and end on the same calendar day.")

        # Venue must be active to accept new bookings
        if venue and not venue.is_active:
            raise forms.ValidationError("This venue is inactive and cannot accept new bookings.")

        # Overlap (no change): intervals [A,B) and [C,D) overlap if A < D and C < B
        if start and end and venue:
            qs = Booking.objects.filter(venue=venue).exclude(pk=getattr(self.instance, "pk", None))
            if qs.filter(Q(start__lt=end) & Q(end__gt=start)).exists():
                raise forms.ValidationError("This time slot overlaps an existing booking for this venue.")

        # Daily cap: A user can only book up to 8 hours per day (sum across venues).
        # Count PENDING + APPROVED (rejected doesn’t count).
        if start and end and self._user and getattr(self._user, "is_authenticated", False):
            duration = end - start
            day = localdate(start)
            day_start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)

            # sum durations for user's bookings on that date (not REJECTED)
            existing = (
                Booking.objects.filter(
                    created_by=self._user,
                    start__gte=day_start,
                    end__lte=day_end,
                )
                .exclude(status=Booking.Status.REJECTED)
                .exclude(pk=getattr(self.instance, "pk", None))
            )

            # annotate each with (end - start) and sum
            dur_expr = ExpressionWrapper(F("end") - F("start"), output_field=DurationField())
            agg = existing.aggregate(total=Sum(dur_expr))
            total = agg["total"] or timedelta(0)
            if total + duration > timedelta(hours=8):
                raise forms.ValidationError("Daily limit exceeded: you can only book up to 8 hours per day.")

        return cleaned
