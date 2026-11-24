from django.contrib import admin

from apps.core.admin_mixins import ImagePreviewMixin

from .models import Certification


@admin.register(Certification)
class CertificationAdmin(ImagePreviewMixin, admin.ModelAdmin):
    preview_field = "certificate"
    list_display = (
        "name", "issuing_organization", "issue_date", "expiry_date",
        "display_order", "image_preview",
    )
    list_editable = ("display_order",)
    list_filter = ("issuing_organization", "issue_date")
    search_fields = ("name", "issuing_organization", "credential_id")
    ordering = ("display_order", "-issue_date")
    readonly_fields = ("image_preview", "created_at", "updated_at")
