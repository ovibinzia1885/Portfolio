from django.core.validators import FileExtensionValidator
from django.db import models

from apps.core.models import OrderedModel


class Certification(OrderedModel):
    name = models.CharField(max_length=200)
    issuing_organization = models.CharField(max_length=200)
    issue_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    credential_id = models.CharField(max_length=100, blank=True)
    credential_url = models.URLField(blank=True)
    certificate = models.FileField(
        upload_to="certifications/",
        blank=True,
        validators=[FileExtensionValidator(["pdf", "jpg", "jpeg", "png", "webp"])],
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

    def __str__(self):
        return f"{self.name} - {self.issuing_organization}"
