from __future__ import annotations

from django.conf import settings
from django.db import models
from django.db.models import Q, UniqueConstraint, PROTECT

# IMPORTANT: Use "accounts.Sport" as a string to avoid cross-app import cycles.


class PositionGroup(models.Model):
    """
    Logical bucket within a sport (Defense, Attack, Singles, Doubles).
    Created by admin/coach from the UI per sport.
    """
    sport = models.ForeignKey("accounts.Sport", on_delete=models.CASCADE, related_name="position_groups")
    name = models.CharField(max_length=64)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sport_id", "order", "name"]
        unique_together = [("sport", "name")]

    def __str__(self) -> str:
        return f"{self.sport.name} · {self.name}"


class Position(models.Model):
    """
    A concrete position like GK, DF, MF, FW, BAT, BWL, AR, WK, etc.
    Per-position lineup constraints help validate lineups.
    """
    sport = models.ForeignKey("accounts.Sport", on_delete=models.CASCADE, related_name="positions")
    group = models.ForeignKey(PositionGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name="positions")
    name = models.CharField(max_length=64)
    code = models.CharField(max_length=16, help_text="Short code: e.g., GK, DF, BAT")
    min_per_lineup = models.PositiveSmallIntegerField(default=0)
    max_per_lineup = models.PositiveSmallIntegerField(default=11)
    is_unique = models.BooleanField(default=False, help_text="If true, allow at most 1 in a lineup (e.g., GK, WK)")

    class Meta:
        ordering = ["sport_id", "group_id", "name"]
        constraints = [
            UniqueConstraint(fields=["sport", "code"], name="unique_position_code_per_sport"),
        ]

    def __str__(self) -> str:
        return f"{self.sport.name} · {self.name} ({self.code})"


class Formation(models.Model):
    """
    Formation template, made of child rows in FormationPosition (no JSON).
    Example: 4-3-3 stored as rows: DF=4, MF=3, FW=3, GK=1.
    """
    sport = models.ForeignKey("accounts.Sport", on_delete=models.CASCADE, related_name="formations")
    name = models.CharField(max_length=64)

    class Meta:
        ordering = ["sport_id", "name"]
        unique_together = [("sport", "name")]

    def __str__(self) -> str:
        return f"{self.sport.name} · {self.name}"

    def total_players(self) -> int:
        return sum(fp.count for fp in self.positions.all())


class FormationPosition(models.Model):
    """
    Child rows for a Formation: which Position and how many.
    """
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name="positions")
    position = models.ForeignKey(Position, on_delete=PROTECT, related_name="formation_rows")
    count = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["id"]
        constraints = [
            UniqueConstraint(fields=["formation", "position"], name="unique_position_per_formation"),
        ]

    def __str__(self) -> str:
        return f"{self.formation.name}: {self.position.code} x{self.count}"


class Team(models.Model):
    """
    Team tied to a sport from accounts.Sport. Coach/captain are Users.
    """
    sport = models.ForeignKey("accounts.Sport", on_delete=models.CASCADE, related_name="teams")
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="teams_created"
    )
    coach = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="teams_coached"
    )
    captain = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="teams_captained"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    home_venues = models.ManyToManyField(
        "facilities.Venue", blank=True, related_name="home_teams", help_text="Preferred home grounds/courts"
    )

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="TeamMembership", related_name="teams"
    )

    class Meta:
        ordering = ["sport_id", "name"]
        unique_together = [("sport", "name")]

    def __str__(self) -> str:
        return f"{self.name} ({self.sport.name})"


class TeamMembership(models.Model):
    class Role(models.TextChoices):
        COACH = "coach", "Coach"
        CAPTAIN = "captain", "Captain"
        PLAYER = "player", "Player"
        MANAGER = "manager", "Manager"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="team_memberships")
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.PLAYER)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    jersey_no = models.PositiveSmallIntegerField(null=True, blank=True)

    primary_position = models.ForeignKey(
        Position, null=True, blank=True, on_delete=models.SET_NULL, related_name="primary_members"
    )
    secondary_position = models.ForeignKey(
        Position, null=True, blank=True, on_delete=models.SET_NULL, related_name="secondary_members"
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["team_id", "user_id"]
        constraints = [
            UniqueConstraint(fields=["team", "user"], name="unique_user_per_team"),
            UniqueConstraint(fields=["team", "jersey_no"], name="unique_jersey_per_team", condition=Q(jersey_no__isnull=False)),
        ]

    def __str__(self) -> str:
        return f"{self.user} @ {self.team} [{self.role}/{self.status}]"
