from django.contrib import admin

from .admin_mixins import ImagePreviewMixin
from .models import Profile, SiteSection


@admin.register(Profile)
class ProfileAdmin(ImagePreviewMixin, admin.ModelAdmin):
    preview_field = "photo"
    list_display = ("full_name", "headline", "email", "image_preview")
    search_fields = ("full_name", "headline", "email")
    readonly_fields = ("image_preview", "created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("full_name", "headline", "short_intro", "bio", "photo", "image_preview")}),
        ("Hero & availability", {"fields": ("hero_greeting", "hero_button_label", "is_available", "availability_text")}),
        ("Contact", {"fields": ("email", "phone", "location")}),
        ("CV", {"fields": ("resume",)}),
        ("Links", {"fields": ("github_url", "linkedin_url", "google_scholar_url", "facebook_url", "twitter_url")}),
        ("Website", {"fields": ("show_visitor_count", "created_at", "updated_at")}),
    )

    def has_add_permission(self, request):
        # The website shows a single profile: once it exists, edit it instead of adding another.
        return super().has_add_permission(request) and not Profile.objects.exists()


@admin.register(SiteSection)
class SiteSectionAdmin(admin.ModelAdmin):
    list_display = ("__str__", "title", "display_order", "is_visible")
    list_editable = ("display_order", "is_visible")
    readonly_fields = ("key",)
    fieldsets = (
        (None, {"fields": ("key", "is_visible", "display_order", "label", "icon")}),
        ("Home page", {"fields": ("eyebrow", "title", "subtitle")}),
        ("Own page", {"fields": ("page_title", "page_subtitle"),
                      "description": "Only for sections with their own page: Projects, Certifications, Blog, Research, Contact."}),
    )

    # The list of sections is fixed by the website; they can be edited or hidden, not added or deleted.
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
