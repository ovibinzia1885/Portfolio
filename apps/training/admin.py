from django.contrib import admin

from apps.core.admin_mixins import ImagePreviewMixin

from .models import Training


@admin.register(Training)
class TrainingAdmin(ImagePreviewMixin, admin.ModelAdmin):
    preview_field = "certificate"
    list_display = ("title", "provider", "start_date", "end_date", "display_order", "image_preview")
    list_editable = ("display_order",)
    list_filter = ("provider", "start_date")
    search_fields = ("title", "provider", "location")
    ordering = ("display_order", "-start_date")
    readonly_fields = ("image_preview", "created_at", "updated_at")
