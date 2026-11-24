from django.db import models
from django.utils import timezone


class Event(models.Model):
    STATUS_CHOICES = (
        ("Active", "Active"),
        ("Upcoming", "Upcoming"),
        ("Completed", "Completed"),
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    access_code = models.CharField(max_length=50, unique=True, db_index=True)
    venue = models.CharField(max_length=255, default="RealSuccess Center")
    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField(default=timezone.localdate)
    days_duration = models.PositiveIntegerField(default=3)
    total_tickets = models.PositiveIntegerField(default=400)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Active")
    banner_image = models.ImageField(upload_to="events/banners/", blank=True, null=True)
    qr_code_url = models.CharField(max_length=500, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date", "-created_at"]
        verbose_name = "Event"
        verbose_name_plural = "Events"

    def __str__(self):
        return f"{self.name} ({self.access_code})"

    @property
    def attendees_count(self):
        """Count checked-in attendees"""
        return self.tickets.filter(check_in_status="Checked In").count()

    @property
    def confirmed_registrations(self):
        """Count registered attendees"""
        return self.tickets.filter(registration_status="Confirmed").count()


class EventStory(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="stories")
    title = models.CharField(max_length=255)
    video_url = models.URLField(blank=True, default="")
    thumbnail = models.ImageField(upload_to="events/stories/", blank=True, null=True)
    duration = models.CharField(max_length=50, default="2:30")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "-created_at"]
        verbose_name = "Event Story"
        verbose_name_plural = "Event Stories"

    def __str__(self):
        return f"{self.title} - {self.event.name}"
