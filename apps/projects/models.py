from django.db import models
from django.urls import reverse

from apps.core.models import OrderedModel
from apps.core.utils import unique_slugify


class ProjectType(models.TextChoices):
    CLIENT = "client", "Client Project"
    PERSONAL = "personal", "Personal Project"


class Project(OrderedModel):
    project_type = models.CharField(
        max_length=10, choices=ProjectType.choices, default=ProjectType.PERSONAL
    )
    client_name = models.CharField(
        max_length=150, blank=True, help_text="Only for client projects (optional)."
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True, allow_unicode=True)
    summary = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    technologies = models.CharField(
        max_length=300, blank=True, help_text="Comma separated"
    )
    live_url = models.URLField(blank=True)
    repository_url = models.URLField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)

    class Meta(OrderedModel.Meta):
        ordering = ["display_order", "-start_date"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("projects:detail", args=[self.slug])

    @property
    def technology_list(self):
        return [t.strip() for t in self.technologies.split(",") if t.strip()]

    @property
    def cover_image(self):
        """First image by order (used as the card thumbnail)."""
        return self.images.first()

    def __str__(self):
        return self.title


class ProjectImage(OrderedModel):
    """Multiple thumbnails / screenshots per project."""

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="projects/")
    caption = models.CharField(max_length=200, blank=True)

    class Meta(OrderedModel.Meta):
        ordering = ["display_order", "id"]

    def __str__(self):
        return f"{self.project.title} image #{self.pk}"
