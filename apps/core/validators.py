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
        limit_mb = self.max_mb or getattr(settings, "MAX_UPLOAD_MB", 5)
        if file.size > limit_mb * 1024 * 1024:
            raise ValidationError(
                f"File is too large ({file.size / 1024 / 1024:.1f} MB). Maximum size is {limit_mb} MB.",
                code="file_too_large",
            )

    def __eq__(self, other):
        return isinstance(other, MaxFileSizeValidator) and self.max_mb == other.max_mb


max_file_size = MaxFileSizeValidator()
image_validators = [FileExtensionValidator(IMAGE_EXTENSIONS), max_file_size]
document_validators = [FileExtensionValidator(DOCUMENT_EXTENSIONS), max_file_size]
pdf_validators = [FileExtensionValidator(["pdf"]), max_file_size]
resume_validators = [FileExtensionValidator(["pdf", "doc", "docx"]), max_file_size]
