"""Reusable upload validators (file type + size) for all FileField/ImageField."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.deconstruct import deconstructible

IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp", "gif"]
DOCUMENT_EXTENSIONS = ["pdf", "jpg", "jpeg", "png", "webp"]


@deconstructible
class MaxFileSizeValidator:
    """Reject files larger than `max_mb` megabytes (default: settings.MAX_UPLOAD_MB)."""

    def __init__(self, max_mb=None):
        self.max_mb = max_mb

    def __call__(self, file):
        # Only new uploads are checked. A file already saved earlier is not re-read on every save,
        # so a record can still be edited if its file went missing on disk or the limit was lowered.
        if getattr(file, "_committed", False):
            return
        limit_mb = self.max_mb or getattr(settings, "MAX_UPLOAD_MB", 5)
        try:
            size = file.size
        except OSError:
            raise ValidationError("The uploaded file could not be read.", code="file_unreadable")
        if size > limit_mb * 1024 * 1024:
            raise ValidationError(
                f"File is too large ({size / 1024 / 1024:.1f} MB). Maximum size is {limit_mb} MB.",
                code="file_too_large",
            )

    def __eq__(self, other):
        return isinstance(other, MaxFileSizeValidator) and self.max_mb == other.max_mb


max_file_size = MaxFileSizeValidator()
image_validators = [FileExtensionValidator(IMAGE_EXTENSIONS), max_file_size]
document_validators = [FileExtensionValidator(DOCUMENT_EXTENSIONS), max_file_size]
pdf_validators = [FileExtensionValidator(["pdf"]), max_file_size]
resume_validators = [FileExtensionValidator(["pdf", "doc", "docx"]), max_file_size]
