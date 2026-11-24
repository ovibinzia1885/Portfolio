from django.core.validators import FileExtensionValidator
from django.db import models

from apps.core.models import OrderedModel


class Training(OrderedModel):
    title = models.CharField(max_length=200)
    provider = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    duration = models.CharField(max_length=60, blank=True, help_text="e.g. 3 months")
    description = models.TextField(blank=True)
    certificate = models.FileField(
        upload_to="training/",
        blank=True,
        validators=[FileExtensionValidator(["pdf", "jpg", "jpeg", "png", "webp"])],
    )

    class Meta(OrderedModel.Meta):
        ordering = ["display_order", "-start_date"]

    def __str__(self):
        return f"{self.title} - {self.provider}"
