from django.conf import settings

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
        "visitor_total": _visitor_total(profile),
    }


def _visitor_total(profile):
    if not profile or not profile.show_visitor_count:
        return None
    from apps.analytics.stats import total_visitors

    return total_visitors()
