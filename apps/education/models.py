from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import OrderedModel
from apps.core.utils import format_date_range, format_duration
from apps.core.validators import document_validators


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
        validators=document_validators,
    )
    institution_website = models.URLField(blank=True)

    class Meta(OrderedModel.Meta):
        ordering = ["display_order", "-start_date"]
        verbose_name_plural = "education"

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date cannot be before start date."})
        if self.cgpa is not None and self.scale and self.cgpa > self.scale:
            raise ValidationError({"cgpa": "CGPA cannot be greater than the scale."})

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
