from django.db import models

class Player(models.Model):
    full_name = models.CharField(max_length=255, db_index=True)
    sport = models.CharField(max_length=100, db_index=True)
    bio = models.TextField(blank=True)
    achievements = models.TextField(blank=True)

    class Meta:
        indexes = [models.Index(fields=["full_name"]), models.Index(fields=["sport"])]
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name
