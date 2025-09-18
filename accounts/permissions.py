# accounts/permissions.py
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin

User = get_user_model()

def is_admin_like(user: User) -> bool:
    return bool(user.is_authenticated and (user.is_staff or getattr(user, "role", None) in {"admin", "staff"}))

def is_admin_or_coach(user: User) -> bool:
    return bool(user.is_authenticated and (user.is_superuser or getattr(user, "role", None) in {"admin", "coach"}))

def admin_required(view_func=None, login_url="accounts:login"):
    checker = user_passes_test(is_admin_like, login_url=login_url)
    return checker if view_func is None else checker(view_func)

def admin_or_coach_required(view_func=None, login_url="accounts:login"):
    checker = user_passes_test(is_admin_or_coach, login_url=login_url)
    return checker if view_func is None else checker(view_func)

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return is_admin_like(user)
