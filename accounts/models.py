#accounts/models.py
from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models
from django.db.models import Q


class UserManager(DjangoUserManager):
    use_in_migrations = True

    def create_user(self, username, email=None, password=None, **extra_fields):
        # Default: not staff, not superuser, guest role
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", User.Roles.GUEST)
        # Normalize email early
        if email:
            email = email.strip().lower()
        return super().create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        # Superusers must be staff + superuser + ADMIN role
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
    Custom user with a single primary role for navigation/permissions.
    Keep it boring and predictable. Future player profile lives in players app.
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

    # Smarter manager
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
