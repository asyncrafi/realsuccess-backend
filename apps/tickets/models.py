import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.events.models import Event


class Ticket(models.Model):
    TICKET_TYPE_CHOICES = (
        ("VIP", "VIP"),
        ("General", "General"),
        ("Executive", "Executive"),
    )
    REGISTRATION_STATUS_CHOICES = (
        ("Confirmed", "Confirmed"),
        ("Pending", "Pending"),
        ("Cancelled", "Cancelled"),
    )
    CHECKIN_STATUS_CHOICES = (
        ("Checked In", "Checked In"),
        ("Not Checked In", "Not Checked In"),
    )

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tickets")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets"
    )
    ticket_id = models.CharField(max_length=50, unique=True, db_index=True)
    attendee_name = models.CharField(max_length=200)
    attendee_email = models.EmailField()
    attendee_phone = models.CharField(max_length=30, blank=True, default="")
    attendee_avatar = models.ImageField(upload_to="attendees/avatars/", blank=True, null=True)

    ticket_type = models.CharField(max_length=50, choices=TICKET_TYPE_CHOICES, default="General")
    registration_status = models.CharField(
        max_length=50,
        choices=REGISTRATION_STATUS_CHOICES,
        default="Confirmed"
    )
    check_in_status = models.CharField(
        max_length=50,
        choices=CHECKIN_STATUS_CHOICES,
        default="Not Checked In"
    )
    check_in_time_slot = models.CharField(max_length=50, default="8:00 AM")
    checked_in_at = models.DateTimeField(null=True, blank=True)

    access_code = models.CharField(max_length=50, blank=True, default="")
    qr_code_data = models.TextField(blank=True, default="")
    price = models.CharField(max_length=50, default="$1,000")
    seat_no = models.CharField(max_length=50, blank=True, default="General Area")
    issue_date = models.DateField(default=timezone.now)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"

    def __str__(self):
        return f"{self.ticket_id} - {self.attendee_name} ({self.ticket_type})"

    def save(self, *args, **kwargs):
        if not self.ticket_id:
            year = timezone.now().year
            rand_code = uuid.uuid4().hex[:6].upper()
            self.ticket_id = f"RS-{year}-{rand_code}"
        if not self.qr_code_data:
            self.qr_code_data = f"REALSUCCESS_TICKET:{self.ticket_id}"
        if not self.access_code and self.event:
            self.access_code = self.event.access_code
        super().save(*args, **kwargs)

    def check_in(self):
        self.check_in_status = "Checked In"
        self.checked_in_at = timezone.now()
        self.save()
