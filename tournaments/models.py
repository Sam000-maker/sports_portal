from django.db import models

class Tournament(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)

    class Meta:
        indexes = [models.Index(fields=["name"])]
        ordering = ["-start_date", "name"]

    def __str__(self):
        return self.name

class Match(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="matches")
    team_a = models.CharField(max_length=128)
    team_b = models.CharField(max_length=128)
    scheduled_at = models.DateTimeField(db_index=True)
    score_a = models.PositiveIntegerField(default=0)
    score_b = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [models.Index(fields=["scheduled_at"])]
        ordering = ["scheduled_at"]

    def __str__(self):
        return f"{self.team_a} vs {self.team_b}"
