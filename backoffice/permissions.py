from django.contrib.auth import get_user_model

User = get_user_model()

def is_admin_like(user: User) -> bool:
    # Centralized gatekeeper. Mirrors accounts.User.is_admin_like
    return bool(user.is_authenticated and (user.is_staff or getattr(user, "role", None) in {"admin", "staff"}))

def is_superuser(user: User) -> bool:
    return bool(user.is_authenticated and user.is_superuser)
