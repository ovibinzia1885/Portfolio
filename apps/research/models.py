from django.core.validators import FileExtensionValidator
from django.db import models

from apps.core.models import OrderedModel


class Research(OrderedModel):
    class PublicationType(models.TextChoices):
        JOURNAL = "journal", "Journal Article"
        CONFERENCE = "conference", "Conference Paper"
        THESIS = "thesis", "Thesis"
        PREPRINT = "preprint", "Preprint"
        OTHER = "other", "Other"

    title = models.CharField(max_length=300)
    authors = models.CharField(max_length=300, help_text="Comma separated")
    publication_type = models.CharField(
        max_length=20, choices=PublicationType.choices, default=PublicationType.JOURNAL
    )
    venue = models.CharField(
        "Journal / Conference", max_length=250, blank=True
    )
    publication_date = models.DateField(null=True, blank=True)
    abstract = models.TextField(blank=True)
    doi = models.CharField("DOI", max_length=100, blank=True)
    url = models.URLField(blank=True)
    pdf = models.FileField(
        upload_to="research/",
        blank=True,
        validators=[FileExtensionValidator(["pdf"])],
    )

    class Meta(OrderedModel.Meta):
        ordering = ["display_order", "-publication_date"]
        verbose_name_plural = "research"

    def __str__(self):
        return self.title
