from .models import Profile


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
    }
