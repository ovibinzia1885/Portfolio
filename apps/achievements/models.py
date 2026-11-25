from django.db import models

from apps.core.models import OrderedModel
from apps.core.validators import document_validators, image_validators


class Achievement(OrderedModel):
    title = models.CharField(max_length=200)
    organization = models.CharField(max_length=200, blank=True)
    date = models.DateField(
        help_text="If only the year is known, use 1 January of that year (only the year is shown)."
    )
    description = models.TextField(blank=True)
    image = models.ImageField(
        "Photo", upload_to="achievements/", blank=True, validators=image_validators,
        help_text="Card photo, e.g. receiving the award.",
    )
    certificate = models.FileField(
        upload_to="achievements/certificates/", blank=True, validators=document_validators,
        help_text="Optional certificate, image or PDF (opens in the Preview popup).",
    )
    url = models.URLField(blank=True)

    class Meta(OrderedModel.Meta):
        ordering = ["display_order", "-date"]

    @property
    def certificate_is_pdf(self):
        return bool(self.certificate) and self.certificate.name.lower().endswith(".pdf")

    @property
    def date_label(self):
        """'Mar 2024', or just '2024' when only the year is known (stored as 1 January)."""
        if not self.date:
            return ""
        return str(self.date.year) if (self.date.month, self.date.day) == (1, 1) else self.date.strftime("%b %Y")

    def __str__(self):
        return self.title
