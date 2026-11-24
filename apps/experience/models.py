from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import OrderedModel
from apps.core.utils import format_date_range, format_duration


class Experience(OrderedModel):
    class EmploymentType(models.TextChoices):
        FULL_TIME = "full_time", "Full-time"
        PART_TIME = "part_time", "Part-time"
        CONTRACT = "contract", "Contract"
        FREELANCE = "freelance", "Freelance"
        INTERNSHIP = "internship", "Internship"

    company = models.CharField(max_length=200)
    company_url = models.URLField("Company website", blank=True)
    company_logo = models.ImageField(upload_to="experience/logos/", blank=True)
    designation = models.CharField(max_length=150)
    employment_type = models.CharField(
        max_length=20, choices=EmploymentType.choices, default=EmploymentType.FULL_TIME
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField("Current employment", default=False)
    responsibilities = models.TextField(blank=True)
    technologies = models.CharField(
        max_length=300, blank=True, help_text="Comma separated, e.g. Python, Django"
    )
    achievements = models.TextField(blank=True)

    class Meta(OrderedModel.Meta):
        ordering = ["display_order", "-start_date"]

    def clean(self):
        if self.is_current:
            self.end_date = None
        elif not self.end_date:
            raise ValidationError({"end_date": "End date is required unless current."})
        elif self.start_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date cannot be before start date."})

    @property
    def duration(self):
        return format_duration(self.start_date, None if self.is_current else self.end_date)

    @property
    def date_range(self):
        return format_date_range(self.start_date, self.end_date, present=self.is_current)

    @property
    def technology_list(self):
        return [t.strip() for t in self.technologies.split(",") if t.strip()]

    def __str__(self):
        return f"{self.designation} at {self.company}"
