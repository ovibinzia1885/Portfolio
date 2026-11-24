from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import OrderedModel


class MainCategory(models.TextChoices):
    TECHNICAL = "technical", "Technical Skills"
    PROJECT_MANAGEMENT = "project_management", "Project Management Skills"
    SOFT = "soft", "Soft Skills"


class SkillSubcategory(OrderedModel):
    """Second-level grouping, e.g. Technical -> API Testing."""

    main_category = models.CharField(
        max_length=20, choices=MainCategory.choices, default=MainCategory.TECHNICAL
    )
    name = models.CharField(max_length=120)

    class Meta(OrderedModel.Meta):
        ordering = ["main_category", "display_order", "name"]
        verbose_name_plural = "skill subcategories"
        constraints = [
            models.UniqueConstraint(
                fields=["main_category", "name"], name="unique_subcategory_per_main"
            )
        ]

    def __str__(self):
        return f"{self.get_main_category_display()} / {self.name}"


class Skill(OrderedModel):
    class Level(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"
        EXPERT = "expert", "Expert"

    name = models.CharField("Skill name", max_length=100)
    main_category = models.CharField(
        max_length=20, choices=MainCategory.choices, default=MainCategory.TECHNICAL
    )
    subcategory = models.ForeignKey(
        SkillSubcategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="skills",
    )
    experience_level = models.CharField(
        max_length=20, choices=Level.choices, default=Level.INTERMEDIATE
    )

    class Meta(OrderedModel.Meta):
        ordering = ["main_category", "subcategory__display_order", "display_order", "name"]

    def clean(self):
        if self.subcategory and self.subcategory.main_category != self.main_category:
            raise ValidationError(
                {"subcategory": "Subcategory does not belong to the selected main category."}
            )

    def __str__(self):
        return self.name
