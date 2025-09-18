# admissions/models.py
from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
    FileExtensionValidator,
)
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


def validate_file_size(f):
    max_mb = 5
    if f.size > max_mb * 1024 * 1024:
        raise ValidationError(f"File too large. Max size is {max_mb} MB.")


def validate_image_size(f):
    max_mb = 3
    if f.size > max_mb * 1024 * 1024:
        raise ValidationError(f"Profile photo too large. Max size is {max_mb} MB.")


class ApplicationCycle(models.Model):
    name = models.CharField(max_length=120, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-start_date"]
        indexes = [models.Index(fields=["is_active", "start_date"])]

    def __str__(self) -> str:
        return self.name

    @property
    def public_id(self) -> str:
        return f"CYC-{self.pk:04d}" if self.pk else "CYC-UNSAVED"

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError("End date cannot be before start date.")

    @property
    def is_open(self) -> bool:
        today = timezone.localdate()
        return self.is_active and self.start_date <= today <= self.end_date

    def extend_to(self, new_end_date):
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

    class Sport(models.TextChoices):
        FOOTBALL = "football", "Football"
        BASKETBALL = "basketball", "Basketball"
        VOLLEYBALL = "volleyball", "Volleyball"
        BADMINTON = "badminton", "Badminton"
        CRICKET = "cricket", "Cricket"
        ATHLETICS = "athletics", "Athletics"

    # Applicant linkage
    applicant = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="applications", null=True, blank=True
    )
    cycle = models.ForeignKey(ApplicationCycle, on_delete=models.PROTECT, related_name="applications")

    # Core sports fields
    sport = models.CharField(
        max_length=20,
        choices=Sport.choices,
        db_index=True,
    )
    playing_position = models.CharField(max_length=80, blank=True)
    level = models.CharField(max_length=20, choices=Level.choices, db_index=True)
    years_experience = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(40)], default=0
    )

    # Applicant details on the application itself
    full_name = models.CharField(max_length=150)
    date_of_birth = models.DateField(null=True, blank=True)
    email = models.EmailField()
    phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(r"^[0-9+\-\s]{7,20}$", "Enter a valid phone number.")],
    )
    address_line1 = models.CharField(max_length=200)
    address_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=80, default="India")
    profile_photo = models.ImageField(
        upload_to="admissions/profile/%Y/%m/",
        null=True,
        blank=True,
        validators=[validate_image_size, FileExtensionValidator(["jpg", "jpeg", "png"])],
        help_text="JPG/PNG only. Max 3 MB.",
    )
    consent = models.BooleanField(
        default=False,
        help_text="I declare the information is true and I consent to data processing for admissions.",
    )

    # Academics & achievements
    previous_institution = models.CharField(max_length=200, blank=True)
    academic_summary = models.TextField(blank=True)
    achievements = models.TextField(blank=True)

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

    # Edit lock
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
        return f"{self.full_name or self.applicant} - {self.get_sport_display()} - {self.cycle}"

    def clean(self):
        # Enforce open window only for new records by regular users
        if not self.pk and self.cycle and not self.cycle.is_open:
            raise ValidationError("Applications are closed for this cycle.")
        if not self.consent:
            raise ValidationError("You must provide consent to submit the application.")

    def set_status(self, new_status: str, reviewer: "User", notes: str = ""):
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
