import uuid
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
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Active")
    banner_image = models.ImageField(upload_to="events/banners/", blank=True, null=True)
    qr_registration_token = models.CharField(max_length=64, unique=True, db_index=True, blank=True, default="")
    qr_code_url = models.CharField(max_length=500, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date", "-created_at"]
        verbose_name = "Event"
        verbose_name_plural = "Events"

    def __str__(self):
        return f"{self.name} ({self.access_code})"

    def save(self, *args, **kwargs):
        if not self.qr_registration_token:
            self.qr_registration_token = f"EVT-{uuid.uuid4().hex[:16].upper()}"
        if not self.qr_code_url:
            self.qr_code_url = f"realsuccess://event/{self.qr_registration_token}"
        super().save(*args, **kwargs)

    @property
    def is_free(self):
        return (self.price or 0) <= 0

    @property
    def attendees_count(self):
        """Count checked-in attendees"""
        return self.tickets.filter(check_in_status="Checked In").count()

    @property
    def confirmed_registrations(self):
        """Count paid/confirmed attendees"""
        return self.tickets.filter(payment_status="Paid").count()


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
