from .models import Profile


def site(request):
    """Expose the owner's profile to every template."""
    profile = Profile.objects.first()
    return {
        "profile": profile,
        "site_name": profile.full_name if profile else "Portfolio",
    }
