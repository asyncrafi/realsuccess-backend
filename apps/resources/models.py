from django.db import models
from django.conf import settings
from apps.events.models import Event


class Resource(models.Model):
    FILE_TYPE_CHOICES = (
        ("PDF", "PDF"),
        ("Video", "Video"),
        ("Image", "Image"),
        ("Document", "Document"),
    )
    STATUS_CHOICES = (
        ("Published", "Published"),
        ("Draft", "Draft"),
    )

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="resources")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    category = models.CharField(max_length=100, default="Guides")
    type = models.CharField(max_length=50, choices=FILE_TYPE_CHOICES, default="PDF")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Published")

    file = models.FileField(upload_to="resources/files/", blank=True, null=True)
    file_url = models.URLField(blank=True, default="")
    file_size = models.CharField(max_length=50, default="2.4 MB")
    is_featured = models.BooleanField(default=False)
    download_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_featured", "-created_at"]
        verbose_name = "Resource"
        verbose_name_plural = "Resources"

    def __str__(self):
        return f"{self.title} ({self.type})"

    def record_download(self, user=None):
        self.download_count += 1
        self.save(update_fields=["download_count"])
        if user and user.is_authenticated:
            UserResourceDownload.objects.create(user=user, resource=self)


class UserResourceDownload(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="resource_downloads")
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name="downloads")
    downloaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-downloaded_at"]
        verbose_name = "User Resource Download"
        verbose_name_plural = "User Resource Downloads"

    def __str__(self):
        return f"{self.user.email} -> {self.resource.title}"
