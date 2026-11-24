from django.contrib import admin
from django.utils.html import format_html


class ImagePreviewMixin:
    """Adds an `image_preview` column/readonly field to a ModelAdmin.

    Set `preview_field` to the name of an ImageField/FileField.
    Non-image files (e.g. PDF) show a dash.
    """

    preview_field = "image"
    preview_size = 60

    @staticmethod
    def _is_image(file_field):
        name = getattr(file_field, "name", "") or ""
        return name.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp"))

    @admin.display(description="Preview")
    def image_preview(self, obj):
        file_field = getattr(obj, self.preview_field, None)
        if file_field and self._is_image(file_field):
            return format_html(
                '<img src="{}" style="height:{}px;border-radius:4px;" alt="preview">',
                file_field.url,
                self.preview_size,
            )
        return "-"
