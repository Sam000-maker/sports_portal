# tournaments/models.py
from __future__ import annotations

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Tournament(models.Model):
    class Type(models.TextChoices):
        ROUND_ROBIN = "round_robin", "Round Robin"
        SINGLE_ELIM = "single_elim", "Single Elimination"
        GROUPS_KO = "groups_ko", "Groups + Knockout"

    name = models.CharField(max_length=120)
    sport = models.ForeignKey("accounts.Sport", on_delete=models.CASCADE, related_name="tournaments")
    ttype = models.CharField(max_length=20, choices=Type.choices, default=Type.ROUND_ROBIN)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="tournaments_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "sport", "start_date"],
                name="uniq_tournament_name_sport_start",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.sport.name})"


class TournamentTeam(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="tournament_teams")
    team = models.ForeignKey("players.Team", on_delete=models.CASCADE, related_name="tournament_entries")
    seed = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1)])

    class Meta:
        ordering = ["tournament_id", "seed", "team__name"]
        constraints = [
            models.UniqueConstraint(fields=["tournament", "team"], name="unique_team_per_tournament"),
        ]
        indexes = [
            models.Index(fields=["tournament", "seed"], name="tt_tournament_seed_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.team.name} @ {self.tournament.name}"


class Match(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        COMPLETED = "completed", "Completed"
        WALKOVER = "walkover", "Walkover"

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="matches")
    round_no = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    group_label = models.CharField(max_length=8, blank=True)  # e.g., "A", "B" for groups

    team_a = models.ForeignKey("players.Team", on_delete=models.PROTECT, related_name="matches_as_a")
    team_b = models.ForeignKey("players.Team", on_delete=models.PROTECT, related_name="matches_as_b")

    scheduled_at = models.DateTimeField(null=True, blank=True)
    venue = models.ForeignKey("facilities.Venue", null=True, blank=True, on_delete=models.SET_NULL, related_name="matches")

    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SCHEDULED)
    officials = models.CharField(max_length=200, blank=True)
    result = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ["tournament_id", "round_no", "scheduled_at", "id"]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(team_a=models.F("team_b")),
                name="match_teams_distinct",
            ),
            models.UniqueConstraint(
                fields=["tournament", "round_no", "group_label", "team_a", "team_b"],
                name="uniq_match_per_round_group",
            ),
        ]
        indexes = [
            models.Index(fields=["tournament", "round_no"], name="match_t_round_idx"),
            models.Index(fields=["tournament", "group_label"], name="match_t_group_idx"),
            models.Index(fields=["scheduled_at"], name="match_scheduled_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.tournament.name}: {self.team_a.name} vs {self.team_b.name} (R{self.round_no}{self.group_label or ''})"


class Lineup(models.Model):
    """A chosen lineup for a particular team in a match."""
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="lineups")
    team = models.ForeignKey("players.Team", on_delete=models.CASCADE, related_name="lineups")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["match", "team"], name="uniq_lineup_per_match_team")
        ]

    def __str__(self) -> str:
        return f"Lineup {self.team.name} @ {self.match}"


class LineupEntry(models.Model):
    lineup = models.ForeignKey(Lineup, on_delete=models.CASCADE, related_name="entries")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # Assumes players.Position has a code and (ideally) a sport FK
    position = models.ForeignKey("players.Position", on_delete=models.PROTECT)
    is_bench = models.BooleanField(default=False)

    class Meta:
        ordering = ["is_bench", "position__code", "user__first_name", "id"]
        constraints = [
            models.UniqueConstraint(fields=["lineup", "user"], name="uniq_user_per_lineup"),
        ]

    def __str__(self) -> str:
        return f"{self.user} as {getattr(self.position, 'code', str(self.position))}"
