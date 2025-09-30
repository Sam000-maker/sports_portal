from __future__ import annotations

from django.conf import settings
from django.db import models
from django.db.models import Q, UniqueConstraint


class Venue(models.Model):
    """
    Campus facility: ground, court, hall.
    """
    name = models.CharField(max_length=120, unique=True)
    venue_type = models.CharField(max_length=64, blank=True, help_text="e.g., Football ground, Indoor court")
    capacity = models.PositiveIntegerField(null=True, blank=True)
    location_note = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)  # NEW: manageable in UI

    def __str__(self) -> str:
        return self.name


class VenuePhoto(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="venues/")
    caption = models.CharField(max_length=120, blank=True)

    def __str__(self) -> str:
        return f"{self.venue.name} photo #{self.pk}"


class Booking(models.Model):
    """
    A time slot reservation. Can be attached to a Tournament match or created ad-hoc.
    """
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="bookings")
    start = models.DateTimeField()
    end = models.DateTimeField()

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="facility_bookings"
    )
    purpose = models.CharField(max_length=120, blank=True)
    tournament_match_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)  # FK-like to tournaments.Match

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)  # NEW
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="decided_bookings"
    )  # NEW
    decided_at = models.DateTimeField(null=True, blank=True)  # NEW

    class Meta:
        ordering = ["start"]
        constraints = [
            UniqueConstraint(fields=["venue", "start", "end"], name="unique_exact_slot_per_venue"),
            models.CheckConstraint(name="booking_valid_range", check=Q(end__gt=models.F("start"))),
        ]
        indexes = [
            models.Index(fields=["venue", "start"]),
            models.Index(fields=["status", "start"]),
        ]

    def __str__(self) -> str:
        return f"{self.venue.name} [{self.start:%Y-%m-%d %H:%M} → {self.end:%H:%M}]"
