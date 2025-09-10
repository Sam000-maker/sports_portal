from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import User


@receiver(pre_save, sender=User)
def normalize_email(sender, instance: User, **kwargs):
    # Be consistent, lowercase emails everywhere
    if instance.email:
        instance.email = instance.email.strip().lower()


@receiver(post_save, sender=User)
def ensure_superuser_role(sender, instance: User, created, **kwargs):
    """
    If a superuser is saved with role != admin, fix it.
    This may re-save once; subsequent calls are no-ops.
    """
    if instance.is_superuser and instance.role != User.Roles.ADMIN:
        instance.role = User.Roles.ADMIN
        instance.save(update_fields=["role"])
