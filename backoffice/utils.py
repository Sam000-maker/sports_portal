from functools import wraps
from django.http import HttpResponseForbidden

def staff_or_admin_required(view_func):
    """Allow users flagged as staff or with role=admin/staff to access backoffice."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = request.user
        if user.is_authenticated and (user.is_staff or getattr(user, "role", "") in {"admin", "staff"}):
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("You do not have permission to access the backoffice.")
    return _wrapped
