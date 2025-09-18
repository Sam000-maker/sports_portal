from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models
from django.db.models import Q
from django.dispatch import receiver
from django.db.models.signals import post_migrate

# -----------------------------
# Sports live in accounts
# -----------------------------
class Sport(models.Model):
    class Code(models.TextChoices):
        FOOTBALL = "football", "Football"
        BASKETBALL = "basketball", "Basketball"
        VOLLEYBALL = "volleyball", "Volleyball"
        BADMINTON = "badminton", "Badminton"
        CRICKET = "cricket", "Cricket"
        ATHLETICS = "athletics", "Athletics"

    # Store the canonical code; display comes from the enum's label
    code = models.CharField(
        max_length=32,
        choices=Code.choices,
        unique=True,
        db_index=True,
    )

    class Meta:
        ordering = ["code"]
        verbose_name = "Sport"
        verbose_name_plural = "Sports"

    def __str__(self) -> str:
        return self.get_code_display()

    @property
    def name(self) -> str:
        # Backwards-friendly alias if you used `name` in templates
        return self.get_code_display()


class UserManager(DjangoUserManager):
    use_in_migrations = True

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", User.Roles.GUEST)
        if email:
            email = email.strip().lower()
        return super().create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Roles.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        if extra_fields.get("role") != User.Roles.ADMIN:
            raise ValueError("Superuser must have role=ADMIN.")
        if email:
            email = email.strip().lower()
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom user with a single primary role.
    Sports are attached directly so admin/coach approvals can promote and copy selections.
    """
    class Roles(models.TextChoices):
        ADMIN = "admin", "Admin"
        COACH = "coach", "Coach"
        STAFF = "staff", "Staff"
        STUDENT = "student", "Student"
        GUEST = "guest", "Guest"  # Default

    role = models.CharField(
        max_length=20, choices=Roles.choices, default=Roles.GUEST, db_index=True
    )
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)

    # user’s approved sports live here
    sports = models.ManyToManyField(Sport, blank=True, related_name="users")

    objects = UserManager()

    def is_admin_like(self) -> bool:
        return bool(self.is_staff or self.role in {self.Roles.ADMIN, self.Roles.STAFF})

    def __str__(self) -> str:
        return f"{self.username} ({self.get_role_display()})"

    class Meta:
        constraints = [
            # If is_superuser then role must be 'admin'
            models.CheckConstraint(
                name="superuser_requires_admin_role",
                check=Q(is_superuser=False) | Q(role="admin"),
            ),
        ]


class RoleChangeLog(models.Model):
    target = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="role_change_events",
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="role_changes_made",
    )
    old_role = models.CharField(max_length=20)
    new_role = models.CharField(max_length=20)
    reason = models.CharField(max_length=255, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-changed_at"]
        indexes = [
            models.Index(fields=["changed_at"]),
            models.Index(fields=["old_role", "new_role"]),
        ]

    def __str__(self) -> str:
        return f"{self.changed_by} -> {self.target}: {self.old_role} → {self.new_role} @ {self.changed_at:%Y-%m-%d %H:%M}"


# -------------------------------------------------------
# Player request workflow, managed by admin/coach
# -------------------------------------------------------
class PendingPlayerRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="player_requests"
    )
    sports = models.ManyToManyField(Sport, related_name="pending_requests")
    bio = models.TextField(blank=True)
    achievements = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="player_requests_reviewed",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-submitted_at"]
        constraints = [
            # Only one pending request per user
            models.UniqueConstraint(
                fields=["user", "status"],
                condition=Q(status="pending"),
                name="unique_pending_request_per_user",
            )
        ]

    def __str__(self) -> str:
        return f"PlayerRequest<{self.user} {self.status}>"


# -------------------------------------------------------
# Auto-seed sports after migrate so the profile dropdown isn't empty
# -------------------------------------------------------
@receiver(post_migrate)
def ensure_default_sports(sender, **kwargs):
    # Only seed when the accounts app is migrated
    if sender.label != "accounts":
        return
    for code, _label in Sport.Code.choices:
        Sport.objects.get_or_create(code=code)
