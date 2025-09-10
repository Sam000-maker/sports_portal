# admissions/templatetags/admissions_nav.py
from __future__ import annotations
from django import template
from django.contrib.auth import get_user_model
from admissions.models import SportsQuotaApplication
from admissions.permissions import is_admin_like

register = template.Library()

@register.simple_tag
def pending_admissions_count(user: get_user_model) -> int:
    if not user.is_authenticated or not is_admin_like(user):
        return 0
    return SportsQuotaApplication.objects.filter(status=SportsQuotaApplication.Status.SUBMITTED).count()
