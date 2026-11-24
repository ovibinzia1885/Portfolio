"""Root URL configuration."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.templatetags.static import static as static_url
from django.urls import include, path
from django.views.generic import RedirectView

from apps.core.sitemaps import sitemaps
from apps.core.favicon import favicon
from apps.core.views import robots_txt


class FaviconRedirect(RedirectView):
    """/favicon.ico -> static icon (URL resolved per request, so hashed production names work)."""

    def get_redirect_url(self, *args, **kwargs):
        return static_url("img/favicon.ico")


urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("robots.txt", robots_txt, name="robots"),
    # Browsers ask for /favicon.ico directly (e.g. when viewing the CV PDF)
    path("favicon.ico", FaviconRedirect.as_view(), name="favicon_ico"),
    # Profile photo as a small square image (used as the admin header logo)
    path("favicon-<int:size>.png", favicon, name="favicon"),
    path("projects/", include("apps.projects.urls")),
    path("blog/", include("apps.blogs.urls")),
    path("research/", include("apps.research.urls")),
    path("contact/", include("apps.contact.urls")),
    path("certifications/", include("apps.certifications.urls")),
    path("", include("apps.core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
