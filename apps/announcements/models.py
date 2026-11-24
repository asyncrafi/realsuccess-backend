from django.db import models
from apps.events.models import Event


class Announcement(models.Model):
    PRIORITY_CHOICES = (
        ("Important", "Important"),
        ("Normal", "Normal"),
        ("High Priority", "High Priority"),
    )
    STATUS_CHOICES = (
        ("Published", "Published"),
        ("Draft", "Draft"),
    )

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="announcements")
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=100, default="Schedule Update")
    priority = models.CharField(max_length=50, choices=PRIORITY_CHOICES, default="Important")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Published")
    content = models.TextField(blank=True, default="")

    takeaway_time = models.CharField(max_length=100, blank=True, default="Time: 1:30 PM → 2:00 PM")
    takeaway_venue = models.CharField(max_length=100, blank=True, default="Venue: Main Auditorium")
    published_by = models.CharField(max_length=150, default="RealSuccess Event Team")
    reading_time = models.CharField(max_length=50, default="1 min read")
    is_new = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Announcement"
        verbose_name_plural = "Announcements"

    def __str__(self):
        return f"{self.title} ({self.priority})"


class AnnouncementAttachment(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name="attachments")
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to="announcements/attachments/", blank=True, null=True)
    file_type = models.CharField(max_length=50, default="PDF")
    size = models.CharField(max_length=50, default="1.2 MB")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Announcement Attachment"
        verbose_name_plural = "Announcement Attachments"

    def __str__(self):
        return f"{self.name} ({self.announcement.title})"
