"""Custom admin site: "Ovy Portfolio" branding and app order that follows the website."""

from django.contrib import admin
from django.contrib.admin.apps import AdminConfig

# Order of the apps on the admin dashboard / sidebar (same order as the website)
APP_ORDER = [
    "core", "experience", "education", "skills", "projects", "certifications",
    "achievements", "training", "research", "blogs", "contact", "analytics", "auth",
]


class PortfolioAdminSite(admin.AdminSite):
    site_header = "Ovy Portfolio"
    site_title = "Ovy Portfolio Admin"
    index_title = "Dashboard"

    def get_app_list(self, request, app_label=None):
        apps = super().get_app_list(request, app_label)
        rank = {label: i for i, label in enumerate(APP_ORDER)}
        return sorted(apps, key=lambda app: (rank.get(app["app_label"], len(APP_ORDER)), app["name"]))


class PortfolioAdminConfig(AdminConfig):
    default_site = "config.admin.PortfolioAdminSite"
