"""Create one SiteSection row per home-page section, filled with today's wording."""

from django.db import migrations

# Frozen copy of apps.core.sections.DEFAULTS at the time of this migration
SECTIONS = [
    ("about", "About", "bi-person", "About me", "Who I am", "A short introduction.", "", ""),
    ("education", "Education", "bi-mortarboard", "Education", "Academic background", "Degrees and institutions.", "", ""),
    ("experience", "Experience", "bi-briefcase", "Experience", "Professional journey",
     "Roles, responsibilities and impact.", "", ""),
    ("skills", "Skills", "bi-tools", "Skills", "Skills & expertise", "Grouped by category. Dots show experience level.", "", ""),
    ("projects", "Projects", "bi-layers", "Projects", "Featured projects",
     "Client work and personal projects. Filter by technology.",
     "All projects", "Client work and personal projects. Filter by technology."),
    ("achievements", "Awards", "bi-trophy", "Achievements", "Awards & recognition", "Milestones along the way.", "", ""),
    ("certifications", "Certifications", "bi-award", "Credentials & courses", "Certifications",
     "Verified credentials. Click preview to view the certificate.", "Certifications", ""),
    ("training", "Training", "bi-journal-bookmark", "Training", "Courses & workshops", "Continuous learning.", "", ""),
    ("blogs", "Blog", "bi-journal-text", "Blog", "Latest articles", "Thoughts, tutorials and notes.",
     "Blog", "Articles, tutorials and notes."),
    ("research", "Research", "bi-file-earmark-text", "Research", "Publications & papers", "Academic and applied research.",
     "Research & publications", "Papers, theses and preprints."),
    ("contact", "Contact", "bi-chat-dots", "Contact", "Let's work together", "Send a message and I will get back to you.",
     "Get in touch", "Questions, opportunities or just a hello."),
]
FIELDS = ("key", "label", "icon", "eyebrow", "title", "subtitle", "page_title", "page_subtitle")


def seed(apps, schema_editor):
    SiteSection = apps.get_model("core", "SiteSection")
    for order, values in enumerate(SECTIONS, start=1):
        data = dict(zip(FIELDS, values))
        SiteSection.objects.get_or_create(key=data.pop("key"), defaults={**data, "display_order": order})


class Migration(migrations.Migration):
    dependencies = [("core", "0006_site_sections_availability")]

    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
