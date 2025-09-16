# players/models.py
from django.conf import settings
from django.db import models

class Sport(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class PlayerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='playerprofile'
    )
    full_name = models.CharField(max_length=255)
    sports = models.ManyToManyField(Sport, blank=True)
    bio = models.TextField(blank=True)
    achievements = models.TextField(blank=True)
    stats = models.TextField(blank=True)  # swap to JSONField later if you want structure
    photo = models.ImageField(upload_to="profiles/", null=True, blank=True)

    def __str__(self):
        return f"{self.full_name} ({self.user.username})"

class Team(models.Model):
    name = models.CharField(max_length=100)
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='teams_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through='TeamMembership', related_name='teams'
    )

    def __str__(self):
        return f"{self.name} ({self.sport.name})"

class TeamMembership(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='team_memberships')
    is_approved = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('team', 'user')

    def __str__(self):
        status = "Member" if self.is_approved else "Invited"
        return f"{self.user.username} - {self.team.name} ({status})"

class Gallery(models.Model):
    image = models.ImageField(upload_to="gallery/")
    caption = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='photos'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo {self.id} by {self.uploaded_by.username}"

class Like(models.Model):
    photo = models.ForeignKey(Gallery, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('photo', 'user')

    def __str__(self):
        return f"{self.user.username} 👍 Photo {self.photo.id}"
