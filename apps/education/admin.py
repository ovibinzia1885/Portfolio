from django.contrib import admin

from apps.core.admin_mixins import ImagePreviewMixin

from .models import Education


@admin.register(Education)
class EducationAdmin(ImagePreviewMixin, admin.ModelAdmin):
    preview_field = "certificate"
    list_display = (
        "institution_name", "degree", "field_of_study", "passing_year",
        "cgpa", "scale", "display_order", "image_preview",
    )
    list_editable = ("display_order",)
    list_filter = ("degree", "passing_year")
    search_fields = ("institution_name", "degree", "field_of_study", "department")
    ordering = ("display_order", "-start_date")
    readonly_fields = ("image_preview", "created_at", "updated_at")
