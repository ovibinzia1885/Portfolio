"""Home-page sections and the sidebar menu, driven by the SiteSection table (editable in admin).

Every section has default wording (DEFAULTS), so the site still works if a row is missing.
A section is shown to visitors only when it is switched on AND has content; the site owner (staff)
also sees empty sections, with a hint on how to fill them.

No cache on purpose: the section rows and "which sections have content" are read in ONE query per
request (EXISTS sub-queries), so an edit in the admin is visible immediately on every server process.
"""

from types import SimpleNamespace

from django.db.models import Exists
from django.urls import reverse

# key: (menu label, icon, eyebrow, title, subtitle, page title, page subtitle)
DEFAULTS = {
    "about": ("About", "bi-person", "About me", "Who I am", "A short introduction.", "", ""),
    "education": ("Education", "bi-mortarboard", "Education", "Academic background", "Degrees and institutions.", "", ""),
    "experience": ("Experience", "bi-briefcase", "Experience", "Professional journey",
                   "Roles, responsibilities and impact.", "", ""),
    "skills": ("Skills", "bi-tools", "Skills", "Skills & expertise",
               "Grouped by category. Dots show experience level.", "", ""),
    "projects": ("Projects", "bi-layers", "Projects", "Featured projects",
                 "Client work and personal projects. Filter by technology.",
                 "All projects", "Client work and personal projects. Filter by technology."),
    "achievements": ("Awards", "bi-trophy", "Achievements", "Awards & recognition", "Milestones along the way.", "", ""),
    "certifications": ("Certifications", "bi-award", "Credentials & courses", "Certifications",
                       "Verified credentials. Click preview to view the certificate.", "Certifications", ""),
    "training": ("Training", "bi-journal-bookmark", "Training", "Courses & workshops", "Continuous learning.", "", ""),
    "blogs": ("Blog", "bi-journal-text", "Blog", "Latest articles", "Thoughts, tutorials and notes.",
              "Blog", "Articles, tutorials and notes."),
    "research": ("Research", "bi-file-earmark-text", "Research", "Publications & papers", "Academic and applied research.",
                 "Research & publications", "Papers, theses and preprints."),
    "contact": ("Contact", "bi-chat-dots", "Contact", "Let's work together", "Send a message and I will get back to you.",
                "Get in touch", "Questions, opportunities or just a hello."),
}
FIELDS = ("label", "icon", "eyebrow", "title", "subtitle", "page_title", "page_subtitle")
# Sections that have their own list page; the menu links there instead of to the home-page anchor
LIST_PAGES = {"certifications": "certifications:list", "blogs": "blogs:list", "research": "research:list"}


def _content_queries():
    """One queryset per section: the section has content when it returns at least one row."""
    from apps.achievements.models import Achievement
    from apps.blogs.models import BlogPost
    from apps.certifications.models import Certification
    from apps.education.models import Education
    from apps.experience.models import Experience
    from apps.projects.models import Project
    from apps.research.models import Research
    from apps.skills.models import Skill
    from apps.training.models import Training

    from .models import Profile

    return {
        "about": Profile.objects.all(),  # bio, numbers and CV buttons; the "write your bio" hint is staff-only
        "education": Education.objects.all(),
        "experience": Experience.objects.all(),
        "skills": Skill.objects.all(),
        "projects": Project.objects.filter(is_featured=True),
        "achievements": Achievement.objects.all(),
        "certifications": Certification.objects.all(),
        "training": Training.objects.all(),
        "blogs": BlogPost.objects.published(),
        "research": Research.objects.all(),
    }


def _load():
    from .models import SiteSection

    queries = _content_queries()
    # The EXISTS sub-queries are not tied to the row, so every row carries the same has_* values
    rows =list(SiteSection.objects.annotate(**{f"has_{key}": Exists(qs) for key, qs in queries.items()}))
    if rows:
        presence = {key: getattr(rows[0], f"has_{key}") for key in queries}
    else:  # no section rows at all (should not happen): ask each table directly
        presence = {key: qs.exists() for key, qs in queries.items()}
    presence["contact"] = True

    by_key = {row.key: row for row in rows}
    sections = []
    for order, key in enumerate(DEFAULTS):
        values = dict(zip(FIELDS, DEFAULTS[key]))
        section = SimpleNamespace(key=key, is_visible=True, display_order=order, **values)
        row = by_key.get(key)
        if row:
            section.is_visible, section.display_order = row.is_visible, row.display_order
            for field in FIELDS:  # an empty field in the admin falls back to the default wording
                setattr(section, field, getattr(row, field) or values[field])
        section.template = f"core/sections/{key}.html"
        section.has_content = presence.get(key, False)
        sections.append(section)
    return sorted(sections, key=lambda s: s.display_order)


def all_sections(request=None):
    """All sections in admin order, each with every field filled. Loaded once per request."""
    if request is None:
        return _load()
    if not hasattr(request, "_site_sections"):
        request._site_sections = _load()
    return request._site_sections


def visible_sections(request, is_staff=False):
    """Sections to render on the home page: switched on and with content (staff also see empty ones)."""
    return [s for s in all_sections(request) if s.is_visible and (s.has_content or is_staff)]


def menu_items(request):
    """Sidebar entries: Home + every visible section that has content."""
    home = reverse("core:home")
    on_home = request.path == home
    app = getattr(getattr(request, "resolver_match", None), "app_name", "")
    items = [{"key": "hero", "label": "Home", "icon": "bi-house", "url": f"{home}#hero", "spy": "hero", "active": False}]
    for s in all_sections(request):
        if not (s.is_visible and s.has_content):
            continue
        item = {"key": s.key, "label": s.label, "icon": s.icon, "url": f"{home}#{s.key}", "spy": s.key, "active": False}
        if s.key in LIST_PAGES:
            item.update(url=reverse(LIST_PAGES[s.key]), spy="", active=app == s.key)
        elif s.key == "projects" and app == "projects":
            item.update(url=reverse("projects:list"), active=True)
        elif s.key == "contact" and not on_home:
            item.update(url=reverse("contact:contact"), spy="", active=app == "contact")
        items.append(item)
    return items
