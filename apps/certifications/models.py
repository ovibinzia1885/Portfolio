from django.db import models

from apps.core.models import OrderedModel
from apps.core.validators import document_validators, image_validators


class Certification(OrderedModel):
    name = models.CharField(max_length=200)
    issuing_organization = models.CharField(max_length=200)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    credential_id = models.CharField(max_length=100, blank=True)
    credential_url = models.URLField(blank=True)
    certificate = models.FileField(
        upload_to="certifications/",
        blank=True,
        validators=document_validators,
    )
    preview_image = models.ImageField(
        upload_to="certifications/previews/", blank=True, validators=image_validators,
        help_text="Optional image of a PDF certificate: shown on the card and in Preview "
                  "(the original file stays the download).",
    )

    class Meta(OrderedModel.Meta):
        ordering = ["display_order", "-issue_date"]

    @property
    def is_image(self):
        return bool(self.certificate) and self.certificate.name.lower().endswith(
            (".jpg", ".jpeg", ".png", ".webp")
        )

    @property
    def is_pdf(self):
        return bool(self.certificate) and self.certificate.name.lower().endswith(".pdf")

    @property
    def display_image(self):
        """Image shown on the card / in Preview: preview image, else the certificate itself if it is an image."""
        if self.preview_image:
            return self.preview_image
        return self.certificate if self.is_image else None

    def __str__(self):
        return f"{self.name} - {self.issuing_organization}"
