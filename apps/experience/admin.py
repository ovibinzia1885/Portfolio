from django.contrib import admin

from apps.core.admin_mixins import ImagePreviewMixin

from .models import Experience


@admin.register(Experience)
class ExperienceAdmin(ImagePreviewMixin, admin.ModelAdmin):
    preview_field = "company_logo"
    list_display = (
        "image_preview", "company", "designation", "employment_type",
        "start_date", "end_date", "is_current", "display_order",
    )
    list_display_links = ("company",)
    list_editable = ("display_order",)
    list_filter = ("employment_type", "is_current")
    search_fields = ("company", "designation", "technologies")
    ordering = ("display_order", "-start_date")
    readonly_fields = ("image_preview", "created_at", "updated_at")
