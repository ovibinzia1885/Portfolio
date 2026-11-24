from django.contrib import admin

from .admin_mixins import ImagePreviewMixin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(ImagePreviewMixin, admin.ModelAdmin):
    preview_field = "photo"
    list_display = ("full_name", "headline", "email", "image_preview")
    search_fields = ("full_name", "headline", "email")
    readonly_fields = ("image_preview", "created_at", "updated_at")
