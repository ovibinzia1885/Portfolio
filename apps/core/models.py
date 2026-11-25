from django.db import models

from .validators import image_validators, resume_validators


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
    short_intro = models.CharField(
        max_length=300, blank=True, help_text="One or two lines shown in the hero section."
    )
    bio = models.TextField(blank=True, help_text="Shown in the About section.")
    photo = models.ImageField(upload_to="profile/", blank=True, validators=image_validators)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    location = models.CharField(max_length=150, blank=True)
    resume = models.FileField(
        "CV / Resume", upload_to="resume/", blank=True, validators=resume_validators,
        help_text="PDF recommended (PDF can be previewed in the browser).",
    )
    github_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    google_scholar_url = models.URLField("Google Scholar URL", blank=True)
    show_visitor_count = models.BooleanField(
        default=True, help_text="Show the total number of visitors in the website footer."
    )
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    is_available = models.BooleanField(
        "Show availability", default=True,
        help_text="Show the green availability badge in the sidebar and hero.",
    )
    availability_text = models.CharField(
        max_length=60, blank=True, default="Available for work",
        help_text='Text of the availability badge, e.g. "Available for work" or "Open to freelance".',
    )
    hero_greeting = models.CharField(
        max_length=60, blank=True, default="hello world",
        help_text='Small terminal-style line above the headline ("$ hello world").',
    )
    hero_button_label = models.CharField(
        max_length=40, blank=True, default="View selected work",
        help_text="Label of the main hero button (it scrolls to Projects).",
    )

    @property
    def resume_available(self):
        """True when a CV is set AND its file really exists (a missing file would break the download)."""
        if not self.resume:
            return False
        from django.core.files.storage import FileSystemStorage

        if not isinstance(self.resume.storage, FileSystemStorage):
            return True  # cloud storage: a check would cost a network call on every page; the view still 404s
        try:
            return self.resume.storage.exists(self.resume.name)
        except (OSError, ValueError):
            return False

    @property
    def resume_is_pdf(self):
        """True when a PDF CV is available (only PDFs can be previewed in the browser)."""
        return self.resume_available and self.resume.name.lower().endswith(".pdf")

    def __str__(self):
        return self.full_name


class SiteSection(OrderedModel):
    """Wording, visibility and order of the home-page sections and the sidebar menu."""

    key = models.CharField(max_length=30, unique=True, editable=False)
    label = models.CharField("Menu label", max_length=40, blank=True)
    icon = models.CharField(
        max_length=40, blank=True, help_text='Bootstrap icon name, e.g. "bi-award" (see icons.getbootstrap.com).'
    )
    eyebrow = models.CharField("Small label", max_length=60, blank=True, help_text="Small text above the title.")
    title = models.CharField(max_length=120, blank=True)
    subtitle = models.CharField(max_length=200, blank=True)
    page_title = models.CharField(
        max_length=120, blank=True, help_text="Heading of the section's own page (Projects, Blog, Research, …)."
    )
    page_subtitle = models.CharField(max_length=200, blank=True)
    is_visible = models.BooleanField(
        "Show on website", default=True,
        help_text="Off = hidden from the home page and the menu. Empty sections are hidden from visitors anyway.",
    )

    class Meta(OrderedModel.Meta):
        verbose_name = "site section"

    def __str__(self):
        return self.label or self.key.title()
