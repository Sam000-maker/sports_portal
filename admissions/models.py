# admissions/models.py
from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    FileExtensionValidator,
)
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


def validate_file_size(f):
    # 5 MB cap because people love uploading 48MP scans of their thumb.
    max_mb = 5
    if f.size > max_mb * 1024 * 1024:
        raise ValidationError(f"File too large. Max size is {max_mb} MB.")


class ApplicationCycle(models.Model):
    """
    Admissions happen in cycles (e.g., '2025-26 UG', '2025 PG').
    Multiple cycles can be active in parallel.
    """
    name = models.CharField(max_length=120, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-start_date"]
        indexes = [models.Index(fields=["is_active", "start_date"])]

    def __str__(self) -> str:
        return self.name

    # Human-readable public ID, no DB change required
    @property
    def public_id(self) -> str:
        # CYC-0007 style. Adjust width if you expect > 9999 cycles for some reason.
        return f"CYC-{self.pk:04d}" if self.pk else "CYC-UNSAVED"

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError("End date cannot be before start date.")

    @property
    def is_open(self) -> bool:
        today = timezone.localdate()
        return self.is_active and self.start_date <= today <= self.end_date

    def extend_to(self, new_end_date):
        """
        Extend the cycle’s end_date forward in time. Refuse shrinkage or past dates.
        """
        if new_end_date < self.end_date:
            raise ValidationError("New end date must be after current end date.")
        if new_end_date < timezone.localdate():
            raise ValidationError("New end date cannot be in the past.")
        self.end_date = new_end_date
        self.save(update_fields=["end_date"])


class SportsQuotaApplication(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    class Level(models.TextChoices):
        COLLEGE = "college", "College"
        DISTRICT = "district", "District"
        STATE = "state", "State"
        NATIONAL = "national", "National"
        INTERNATIONAL = "international", "International"

    # TEMPORARILY NULLABLE so you can migrate safely, then backfill, then flip to required.
    applicant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="applications",
        null=True,
        blank=True,
    )
    cycle = models.ForeignKey(ApplicationCycle, on_delete=models.PROTECT, related_name="applications")
    sport = models.CharField(max_length=80, db_index=True)
    playing_position = models.CharField(max_length=80, blank=True)
    level = models.CharField(max_length=20, choices=Level.choices, db_index=True)
    years_experience = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(40)], default=0
    )

    # Academic basics
    previous_institution = models.CharField(max_length=200, blank=True)
    academic_summary = models.TextField(blank=True, help_text="Marks/grades summary or notes.")

    # Achievements
    achievements = models.TextField(blank=True, help_text="Major tournaments, medals, ranks.")

    # Status and audit
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SUBMITTED, db_index=True
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewer = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_sports_applications"
    )
    review_notes = models.TextField(blank=True)

    # Soft lock to prevent edits while review happens
    locked = models.BooleanField(default=False)

    class Meta:
        ordering = ["-submitted_at"]
        indexes = [
            models.Index(fields=["status", "sport"]),
            models.Index(fields=["cycle", "status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["applicant", "cycle", "sport"],
                name="unique_applicant_cycle_sport",
                violation_error_message="You already applied for this sport in the current cycle.",
            )
        ]

    def __str__(self) -> str:
        return f"{self.applicant} - {self.sport} - {self.cycle}"

    def clean(self):
        # Enforce cycle open window for new submissions.
        # Let admins edit regardless during review.
        if not self.pk and self.cycle and not self.cycle.is_open:
            raise ValidationError("Applications are closed for this cycle.")

    def set_status(self, new_status: str, reviewer: "User", notes: str = ""):
        """Centralized status transition with audit timestamps."""
        if new_status not in {s.value for s in self.Status}:
            raise ValidationError("Invalid status.")
        self.status = new_status
        self.reviewer = reviewer
        self.reviewed_at = timezone.now()
        if notes:
            stamp = timezone.now().strftime("%Y-%m-%d %H:%M")
            self.review_notes = (self.review_notes + f"\n[{stamp}] {notes}").strip()
        self.locked = new_status in {self.Status.APPROVED, self.Status.REJECTED}
        self.save(update_fields=["status", "reviewer", "reviewed_at", "review_notes", "locked"])


class ApplicationDocument(models.Model):
    """
    Uploaded proofs: participation/merit certificates, ID, fitness cert, etc.
    """
    class DocType(models.TextChoices):
        PARTICIPATION = "participation", "Participation Certificate"
        MERIT = "merit", "Merit/Medal Certificate"
        ID_PROOF = "id_proof", "ID Proof"
        PHOTO = "photo", "Passport Size Photo"
        MEDICAL = "medical", "Medical Fitness Certificate"
        OTHER = "other", "Other"

    application = models.ForeignKey(
        SportsQuotaApplication, on_delete=models.CASCADE, related_name="documents"
    )
    doc_type = models.CharField(max_length=20, choices=DocType.choices)
    file = models.FileField(
        upload_to="admissions/%Y/%m/",
        validators=[
            FileExtensionValidator(allowed_extensions=["pdf", "jpg", "jpeg", "png"]),
            validate_file_size,
        ],
        help_text="PDF/JPG/PNG only. Max 5 MB.",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
        indexes = [models.Index(fields=["doc_type", "uploaded_at"])]

    def __str__(self) -> str:
        return f"{self.get_doc_type_display()} - {self.application_id}"
