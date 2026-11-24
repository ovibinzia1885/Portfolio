from django.db import models

from apps.core.models import OrderedModel
from apps.core.validators import image_validators


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
    certificate = models.ImageField(
        upload_to="achievements/certificates/", blank=True, validators=image_validators,
        help_text="Optional certificate image (opens in the Preview popup).",
    )
    url = models.URLField(blank=True)

    class Meta(OrderedModel.Meta):
        ordering = ["display_order", "-date"]

    @property
    def date_label(self):
        """'Mar 2024', or just '2024' when only the year is known (stored as 1 January)."""
        if not self.date:
            return ""
        return str(self.date.year) if (self.date.month, self.date.day) == (1, 1) else self.date.strftime("%b %Y")

    def __str__(self):
        return self.title
