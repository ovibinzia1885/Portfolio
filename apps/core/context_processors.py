from django.conf import settings
from django.utils.functional import SimpleLazyObject

from .models import Profile

# CSS/JS files whose change must bypass the browser cache in development
VERSIONED_ASSETS = ("css/main.css", "css/responsive.css", "js/main.js", "css/admin.css")


def asset_version():
    """Development: latest modification time of our CSS/JS, used as ?v= so browsers reload them.
    Production: empty, because ManifestStaticFilesStorage already puts a hash in the file names."""
    if not settings.DEBUG:
        return ""
    mtimes = []
    for name in VERSIONED_ASSETS:
        for folder in settings.STATICFILES_DIRS:
            path = folder / name
            if path.exists():
                mtimes.append(int(path.stat().st_mtime))
    return str(max(mtimes, default=0))


def site(request):
    """Expose the owner's profile and SEO helpers to every template."""
    profile = Profile.objects.first()
    # Canonical URL: path only (drops tracking/filter params), but keeps ?page=N > 1
    canonical = request.build_absolute_uri(request.path)
    page = request.GET.get("page", "")
    if page.isdigit() and page != "1":
        canonical += f"?page={page}"
    og_image = ""
    if profile and profile.photo:
        og_image = request.build_absolute_uri(profile.photo.url)
    return {
        "profile": profile,
        "site_name": profile.full_name if profile else "Portfolio",
        "canonical_url": canonical,
        "default_og_image": og_image,
        "asset_version": asset_version(),
        **_visit_counts(profile),
        **_sections(request),
    }


def _sections(request):
    """Section wording (`sections.about.title`, …) and the sidebar menu. Lazy: only queried when a page uses them."""
    from .sections import all_sections, menu_items

    return {
        "sections": SimpleLazyObject(lambda: {s.key: s for s in all_sections(request)}),
        "menu_items": SimpleLazyObject(lambda: menu_items(request)),
    }


def _visit_counts(profile):
    """Footer numbers: unique visitors and total page views (both all-time)."""
    if not profile or not profile.show_visitor_count:
        return {"visitor_total": None, "view_total": None}
    from apps.analytics.stats import total_views, total_visitors

    return {"visitor_total": total_visitors(), "view_total": total_views()}
