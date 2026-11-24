from django.db import models
from django.urls import reverse

from apps.core.models import OrderedModel
from apps.core.utils import unique_slugify
from apps.core.validators import pdf_validators


class Research(OrderedModel):
    class PublicationType(models.TextChoices):
        JOURNAL = "journal", "Journal Article"
        CONFERENCE = "conference", "Conference Paper"
        THESIS = "thesis", "Thesis"
        PREPRINT = "preprint", "Preprint"
        OTHER = "other", "Other"

    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=320, unique=True, blank=True, allow_unicode=True)
    authors = models.CharField(max_length=300, help_text="Comma separated")
    publication_type = models.CharField(
        max_length=20, choices=PublicationType.choices, default=PublicationType.JOURNAL
    )
    venue = models.CharField(
        "Journal / Conference", max_length=250, blank=True
    )
    indexing = models.CharField(
        "Indexing / Quartile", max_length=60, blank=True,
        help_text="Optional badge, e.g. 'Q2' or 'Q1 · Scopus'.",
    )
    publication_date = models.DateField(
        null=True, blank=True,
        help_text="If only the year is known, use 1 January of that year (only the year is shown).",
    )
    abstract = models.TextField(blank=True)
    doi = models.CharField("DOI", max_length=100, blank=True)
    url = models.URLField(blank=True)
    pdf = models.FileField(upload_to="research/", blank=True, validators=pdf_validators)

    class Meta(OrderedModel.Meta):
        ordering = ["display_order", "-publication_date"]
        verbose_name_plural = "research"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("research:detail", args=[self.slug])

    @property
    def date_label(self):
        """'Feb 2024', or just '2024' when only the year is known (stored as 1 January)."""
        d = self.publication_date
        if not d:
            return ""
        return str(d.year) if (d.month, d.day) == (1, 1) else d.strftime("%b %Y")

    def get_download_url(self):
        return reverse("research:download", args=[self.slug])

    def __str__(self):
        return self.title
