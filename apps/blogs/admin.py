from django.contrib import admin

from apps.core.admin_mixins import ImagePreviewMixin

from .models import BlogPost


@admin.register(BlogPost)
class BlogPostAdmin(ImagePreviewMixin, admin.ModelAdmin):
    preview_field = "cover_image"
    list_display = ("title", "status", "published_at", "image_preview")
    list_filter = ("status", "published_at")
    search_fields = ("title", "excerpt", "tags", "content")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("-published_at", "-created_at")
    date_hierarchy = "published_at"
    readonly_fields = ("image_preview", "created_at", "updated_at")
