from django.db import models

class Facility(models.Model):
    name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    def __str__(self): return self.name

class Booking(models.Model):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name="bookings")
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(db_index=True)
    booked_by = models.CharField(max_length=255)

    class Meta:
        indexes = [models.Index(fields=["start_time"]), models.Index(fields=["end_time"])]
        ordering = ["-start_time"]
