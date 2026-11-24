from django.contrib import admin

from apps.core.admin_mixins import ImagePreviewMixin

from .models import Achievement


@admin.register(Achievement)
class AchievementAdmin(ImagePreviewMixin, admin.ModelAdmin):
    list_display = ("title", "organization", "date", "display_order", "image_preview")
    list_editable = ("display_order",)
    list_filter = ("date",)
    search_fields = ("title", "organization")
    ordering = ("display_order", "-date")
    readonly_fields = ("image_preview", "created_at", "updated_at")
