from django.db import models


class LegalDocument(models.Model):
    title = models.CharField(max_length=100, default="RealSuccess Legal Settings")
    privacy_policy_content = models.TextField(
        default="<h2>Privacy Policy</h2><p>Welcome to RealSuccess. We value your privacy and are committed to protecting your personal data.</p>"
    )
    terms_conditions_content = models.TextField(
        default="<h2>Terms & Conditions</h2><p>By accessing or using the RealSuccess platform, you agree to be bound by these terms.</p>"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Legal Document"
        verbose_name_plural = "Legal Documents"

    def __str__(self):
        return f"{self.title} (Updated {self.updated_at.strftime('%Y-%m-%d %H:%M')})"


class FAQ(models.Model):
    CATEGORY_CHOICES = (
        ("general", "General"),
        ("registration", "Registration & Tickets"),
        ("venue", "Venue & Logistics"),
        ("schedule", "Schedule & Speakers"),
        ("vip", "VIP Perks & Lounge"),
    )

    question = models.CharField(max_length=300)
    answer = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="general")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question
