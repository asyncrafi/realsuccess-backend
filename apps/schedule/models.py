from django.db import models
from django.conf import settings
from apps.events.models import Event


class Speaker(models.Model):
    name = models.CharField(max_length=200)
    role = models.CharField(max_length=200, default="Keynote Speaker")
    organization = models.CharField(max_length=200, blank=True, default="")
    avatar = models.ImageField(upload_to="speakers/avatars/", blank=True, null=True)
    bio = models.TextField(blank=True, default="")
    years_of_experience = models.CharField(max_length=50, blank=True, default="20+ years")
    workshops_conducted = models.CharField(max_length=50, blank=True, default="150+ Conducted")
    specialization = models.CharField(max_length=100, blank=True, default="Commercial")
    industry = models.CharField(max_length=100, blank=True, default="Real Estate")
    areas_of_expertise = models.JSONField(
        default=list,
        blank=True,
        help_text="e.g. ['Leadership', 'Business Growth', 'Personal Development']"
    )
    official_website = models.CharField(max_length=255, blank=True, default="")
    company_name = models.CharField(max_length=200, blank=True, default="")
    is_keynote_spotlight = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_keynote_spotlight", "name"]
        verbose_name = "Speaker"
        verbose_name_plural = "Speakers"

    def __str__(self):
        return f"{self.name} ({self.role})"


class Session(models.Model):
    SESSION_TYPE_CHOICES = (
        ("Keynote", "Keynote"),
        ("Panel", "Panel"),
        ("Workshop", "Workshop"),
        ("Networking", "Networking"),
        ("Breakout", "Breakout"),
    )
    STATUS_CHOICES = (
        ("Published", "Published"),
        ("Draft", "Draft"),
        ("Cancelled", "Cancelled"),
    )

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="sessions")
    day_number = models.PositiveIntegerField(default=1)
    date = models.DateField()
    session_title = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=SESSION_TYPE_CHOICES, default="Keynote")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Published")
    time = models.CharField(max_length=100, help_text="e.g. 09:00 AM – 10:30 AM")
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    venue = models.CharField(max_length=255, default="Main Conference Hall")
    duration = models.CharField(max_length=50, default="90 Minutes")
    speaker = models.ForeignKey(
        Speaker,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions"
    )
    description = models.TextField(blank=True, default="")
    important_notes = models.JSONField(
        default=list,
        blank=True,
        help_text="List of bullet points for session guidelines"
    )
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["date", "start_time", "order"]
        verbose_name = "Session"
        verbose_name_plural = "Sessions"

    def __str__(self):
        return f"{self.session_title} - Day {self.day_number}"


class SessionResource(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="resources")
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="sessions/resources/", blank=True, null=True)
    file_size = models.CharField(max_length=50, default="4.2 MB")
    file_type = models.CharField(max_length=20, default="PDF")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Session Resource"
        verbose_name_plural = "Session Resources"

    def __str__(self):
        return f"{self.title} ({self.session.session_title})"


class SessionBookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="session_bookmarks")
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="bookmarks")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "session")
        verbose_name = "Session Bookmark"
        verbose_name_plural = "Session Bookmarks"

    def __str__(self):
        return f"{self.user.email} -> {self.session.session_title}"
