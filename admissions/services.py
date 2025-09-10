# admissions/services.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import ApplicationCycle


@dataclass
class StartResult:
    cycle: ApplicationCycle
    created: bool


@transaction.atomic
def start_admissions(*, name: str, start_date: date, end_date: date) -> StartResult:
    """
    Start or reactivate a cycle with the given name.
    Multiple active cycles are allowed.
    """
    if start_date > end_date:
        raise ValidationError("Start date must be on or before end date.")

    cycle, created = ApplicationCycle.objects.get_or_create(
        name=name,
        defaults={"start_date": start_date, "end_date": end_date, "is_active": True},
    )
    if not created:
        cycle.start_date = start_date
        cycle.end_date = end_date
        cycle.is_active = True
        cycle.full_clean()
        cycle.save(update_fields=["start_date", "end_date", "is_active"])
    return StartResult(cycle=cycle, created=created)


@transaction.atomic
def stop_admissions(*, cycle_id: Optional[int]) -> Optional[ApplicationCycle]:
    """
    Hard-stop a cycle and push it to 'Past' immediately:
      - Set end_date to yesterday (today - 1 day) so it no longer matches the live window.
      - If start_date would exceed end_date, clamp start_date to end_date.
      - Set is_active = False.
      - Save atomically and return the updated cycle.
    Returns None if the cycle isn't found.
    """
    if cycle_id is None:
        return None

    try:
        cycle = ApplicationCycle.objects.select_for_update().get(pk=cycle_id)
    except ApplicationCycle.DoesNotExist:
        return None

    today = timezone.localdate()
    new_end = today - timedelta(days=1)

    cycle.end_date = new_end
    if cycle.start_date > new_end:
        cycle.start_date = new_end
    cycle.is_active = False

    cycle.full_clean()
    cycle.save(update_fields=["start_date", "end_date", "is_active"])
    return cycle


@transaction.atomic
def extend_admissions(*, cycle_id: int, new_end_date: date) -> ApplicationCycle:
    """
    Extend a specific cycle’s end date.
    Relies on model-level validation to enforce window rules.
    """
    cycle = ApplicationCycle.objects.get(pk=cycle_id)
    cycle.extend_to(new_end_date)
    return cycle
