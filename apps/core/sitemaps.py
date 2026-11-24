"""XML sitemap (/sitemap.xml) for search engines."""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.blogs.models import BlogPost
from apps.projects.models import Project
from apps.research.models import Research


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"

    def items(self):
        return ["core:home", "projects:list", "blogs:list", "research:list", "certifications:list"]

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return 1.0 if item == "core:home" else 0.7


class ProjectSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.8

    def items(self):
        return Project.objects.all()

    def lastmod(self, obj):
        return obj.updated_at


class BlogPostSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return BlogPost.objects.published()

    def lastmod(self, obj):
        return obj.updated_at


class ResearchSitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.6

    def items(self):
        return Research.objects.all()

    def lastmod(self, obj):
        return obj.updated_at


sitemaps = {
    "static": StaticViewSitemap,
    "projects": ProjectSitemap,
    "blog": BlogPostSitemap,
    "research": ResearchSitemap,
}
