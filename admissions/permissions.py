# admissions/permissions.py
from django.contrib.auth import get_user_model
from typing import Any

User = get_user_model()

def is_admin_like(user: Any) -> bool:
    return bool(user.is_authenticated and (user.is_staff or getattr(user, "role", None) in {"admin", "staff"}))
