"""Root URL configuration."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from apps.core.sitemaps import sitemaps
from apps.core.views import robots_txt

admin.site.site_header = "Portfolio administration"
admin.site.site_title = "Portfolio admin"

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("robots.txt", robots_txt, name="robots"),
    path("projects/", include("apps.projects.urls")),
    path("blog/", include("apps.blogs.urls")),
    path("research/", include("apps.research.urls")),
    path("contact/", include("apps.contact.urls")),
    path("certifications/", include("apps.certifications.urls")),
    path("", include("apps.core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
