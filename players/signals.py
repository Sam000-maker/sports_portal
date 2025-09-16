# players/signals.py
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import PlayerProfile

User = get_user_model()

@receiver(post_save, sender=User, dispatch_uid="players_create_profile_for_student")
def create_profile_for_student(sender, instance, created, **kwargs):
    """
    Auto-create PlayerProfile for users whose role is STUDENT.
    Works for new users and when an existing user's role flips to STUDENT.
    """
    # Use the enum value; it's a string under the hood
    Roles = getattr(User, "Roles", None)
    target_value = getattr(Roles, "STUDENT", "student")

    if getattr(instance, "role", None) != target_value:
        return

    # Create if missing
    if not PlayerProfile.objects.filter(user=instance).exists():
        PlayerProfile.objects.create(
            user=instance,
            full_name=(instance.get_full_name() or instance.username),
        )
