from django.core.validators import FileExtensionValidator
from django.db import models

from apps.core.models import OrderedModel
from apps.core.utils import format_date_range, format_duration


class Education(OrderedModel):
    institution_name = models.CharField(max_length=200)
    degree = models.CharField(max_length=150)
    field_of_study = models.CharField(max_length=150)
    department = models.CharField(max_length=150, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    passing_year = models.PositiveSmallIntegerField(null=True, blank=True)
    cgpa = models.DecimalField(
        "CGPA / GPA", max_digits=4, decimal_places=2, null=True, blank=True
    )
    scale = models.DecimalField(
        max_digits=4, decimal_places=2, default=4.00, help_text="e.g. 4.00 or 5.00"
    )
    description = models.TextField(blank=True)
    certificate = models.FileField(
        "Education certificate",
        upload_to="education/certificates/",
        blank=True,
        validators=[FileExtensionValidator(["pdf", "jpg", "jpeg", "png", "webp"])],
    )
    institution_website = models.URLField(blank=True)

    class Meta(OrderedModel.Meta):
        ordering = ["display_order", "-start_date"]
        verbose_name_plural = "education"

    @property
    def duration(self):
        if not self.end_date:
            return "Ongoing"
        return format_duration(self.start_date, self.end_date)

    @property
    def date_range(self):
        return format_date_range(self.start_date, self.end_date, present=True)

    def __str__(self):
        return f"{self.degree} - {self.institution_name}"
