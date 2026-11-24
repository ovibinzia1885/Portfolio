from django.db import models
from django.utils.text import slugify

from apps.core.models import OrderedModel


class Project(OrderedModel):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
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
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

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
