from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base: created/updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class OrderedModel(TimeStampedModel):
    """Abstract base: adds manual display ordering."""

    display_order = models.PositiveIntegerField(
        default=0, help_text="Lower numbers appear first."
    )

    class Meta:
        abstract = True
        ordering = ["display_order"]


class Profile(TimeStampedModel):
    """Site owner's profile (use a single record)."""

    full_name = models.CharField(max_length=150)
    headline = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to="profile/", blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    location = models.CharField(max_length=150, blank=True)
    resume = models.FileField(upload_to="resume/", blank=True)
    github_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)

    def __str__(self):
        return self.full_name
