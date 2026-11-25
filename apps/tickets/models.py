import uuid
from decimal import Decimal
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
    PAYMENT_STATUS_CHOICES = (
        ("Pending Payment", "Pending Payment"),
        ("Paid", "Paid"),
        ("Payment Rejected", "Payment Rejected"),
    )
    TICKET_STATUS_CHOICES = (
        ("Unused", "Unused"),
        ("Used", "Used"),
        ("Cancelled", "Cancelled"),
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
        related_name="tickets",
    )
    ticket_id = models.CharField(max_length=50, unique=True, db_index=True)
    attendee_name = models.CharField(max_length=200)
    attendee_email = models.EmailField()
    attendee_phone = models.CharField(max_length=30, blank=True, default="")
    attendee_avatar = models.ImageField(upload_to="attendees/avatars/", blank=True, null=True)

    ticket_type = models.CharField(max_length=50, choices=TICKET_TYPE_CHOICES, default="General")
    payment_status = models.CharField(
        max_length=30,
        choices=PAYMENT_STATUS_CHOICES,
        default="Pending Payment",
    )
    ticket_status = models.CharField(
        max_length=20,
        choices=TICKET_STATUS_CHOICES,
        default="Unused",
    )
    registration_status = models.CharField(
        max_length=50,
        choices=REGISTRATION_STATUS_CHOICES,
        default="Pending",
    )
    check_in_status = models.CharField(
        max_length=50,
        choices=CHECKIN_STATUS_CHOICES,
        default="Not Checked In",
    )
    check_in_time_slot = models.CharField(max_length=50, default="8:00 AM")
    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_in_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scanned_tickets",
    )

    access_code = models.CharField(max_length=50, blank=True, default="")
    qr_validation_token = models.CharField(max_length=64, unique=True, db_index=True, blank=True, default="")
    qr_code_data = models.TextField(blank=True, default="")
    price_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    price = models.CharField(max_length=50, default="$0.00")
    seat_no = models.CharField(max_length=50, blank=True, default="")
    issue_date = models.DateField(default=timezone.localdate)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"

    def __str__(self):
        return f"{self.ticket_id} - {self.attendee_name} ({self.payment_status} / {self.ticket_status})"

    def sync_statuses(self):
        """Keep legacy registration_status & check_in_status aligned with payment_status & ticket_status."""
        if self.ticket_status == "Cancelled" or self.payment_status == "Payment Rejected":
            self.registration_status = "Cancelled"
        elif self.payment_status == "Paid":
            self.registration_status = "Confirmed"
        else:
            self.registration_status = "Pending"

        if self.ticket_status == "Used":
            self.check_in_status = "Checked In"
        else:
            self.check_in_status = "Not Checked In"

    def save(self, *args, **kwargs):
        if not self.ticket_id:
            year = timezone.now().year
            rand_code = uuid.uuid4().hex[:6].upper()
            self.ticket_id = f"RS-{year}-{rand_code}"
        if not self.qr_validation_token:
            self.qr_validation_token = f"TKT-{uuid.uuid4().hex[:16].upper()}"
        if not self.qr_code_data:
            self.qr_code_data = self.qr_validation_token
        if not self.access_code and self.event:
            self.access_code = self.event.access_code
        if self.event:
            event_price = self.event.price or Decimal("0.00")
            if self.price_amount is None or Decimal(str(self.price_amount)) == Decimal("0.00"):
                self.price_amount = event_price
            self.price = "Free" if Decimal(str(self.price_amount)) <= 0 else f"${Decimal(str(self.price_amount)):,.2f}"
        self.sync_statuses()
        super().save(*args, **kwargs)

    def check_in(self, staff_user=None):
        self.ticket_status = "Used"
        self.check_in_status = "Checked In"
        self.checked_in_at = timezone.now()
        if staff_user and getattr(staff_user, "is_authenticated", False):
            self.checked_in_by = staff_user
        self.save()
