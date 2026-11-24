from django.contrib import admin

from apps.core.admin_mixins import ImagePreviewMixin

from .models import BlogCategory, BlogPost, BlogTag


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(BlogTag)
class BlogTagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(BlogPost)
class BlogPostAdmin(ImagePreviewMixin, admin.ModelAdmin):
    preview_field = "cover_image"
    list_display = ("title", "category", "status", "published_at", "image_preview")
    list_filter = ("status", "category", "tags", "published_at")
    search_fields = ("title", "excerpt", "content")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)
    ordering = ("-published_at", "-created_at")
    date_hierarchy = "published_at"
    readonly_fields = ("image_preview", "created_at", "updated_at")
