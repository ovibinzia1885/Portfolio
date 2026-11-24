from django.contrib import admin
from django.utils.html import format_html

from apps.core.admin_mixins import ImagePreviewMixin

from .models import Project, ProjectImage


class ProjectImageInline(ImagePreviewMixin, admin.TabularInline):
    model = ProjectImage
    extra = 3
    fields = ("image", "image_preview", "caption", "display_order")
    readonly_fields = ("image_preview",)
    preview_size = 80


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "title", "project_type", "cover_preview", "image_count", "is_featured",
        "start_date", "display_order",
    )
    list_editable = ("is_featured", "display_order")
    list_filter = ("project_type", "is_featured")
    search_fields = ("title", "client_name", "summary", "technologies")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("display_order", "-start_date")
    readonly_fields = ("created_at", "updated_at")
    inlines = [ProjectImageInline]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("images")

    @admin.display(description="Cover")
    def cover_preview(self, obj):
        image = obj.images.all()[0] if obj.images.all() else None
        if image:
            return format_html(
                '<img src="{}" style="height:50px;border-radius:4px;" alt="cover">',
                image.image.url,
            )
        return "-"

    @admin.display(description="Images")
    def image_count(self, obj):
        return len(obj.images.all())
