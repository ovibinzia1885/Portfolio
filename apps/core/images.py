"""Automatic image optimisation for every ImageField on upload.

New uploads larger than MAX_IMAGE_PX on their longest side are resized and re-compressed.
Already-stored images are never touched. GIFs (may be animated) are left as they are.
"""

from io import BytesIO

from django.core.files.base import ContentFile
from django.db import models
from django.db.models.signals import pre_save
from PIL import Image, ImageOps

MAX_IMAGE_PX = 1920
JPEG_QUALITY = 85
FORMATS = {"JPEG": "JPEG", "MPO": "JPEG", "PNG": "PNG", "WEBP": "WEBP"}


def optimize_image_file(field_file, max_px=MAX_IMAGE_PX):
    """Resize/compress an uncommitted upload in place. Returns True if changed."""
    if not field_file or getattr(field_file, "_committed", True):
        return False
    try:
        field_file.seek(0)
        img = Image.open(field_file)
        fmt = FORMATS.get(img.format)
        if not fmt or max(img.size) <= max_px:
            field_file.seek(0)
            return False
        img = ImageOps.exif_transpose(img)
        img.thumbnail((max_px, max_px), Image.LANCZOS)
        if fmt == "JPEG" and img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        buffer = BytesIO()
        options = {"optimize": True}
        if fmt in ("JPEG", "WEBP"):
            options["quality"] = JPEG_QUALITY
        img.save(buffer, format=fmt, **options)
    except (OSError, ValueError):  # not a readable image: leave it to field validation
        field_file.seek(0)
        return False
    name = field_file.name
    field_file.file = ContentFile(buffer.getvalue(), name=name)
    return True


IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp")


def optimize_images(sender, instance, **kwargs):
    for field in instance._meta.get_fields():
        if isinstance(field, models.ImageField):
            optimize_image_file(getattr(instance, field.attname))
        elif isinstance(field, models.FileField):  # e.g. a certificate that may be an image or a PDF
            file = getattr(instance, field.attname)
            if file and file.name.lower().endswith(IMAGE_SUFFIXES):
                optimize_image_file(file)


def connect():
    pre_save.connect(optimize_images, dispatch_uid="core.optimize_images")
