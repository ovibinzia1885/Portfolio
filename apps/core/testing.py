"""Shared helpers for the test suites of all apps."""

import shutil
import tempfile
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image

MINIMAL_PDF = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Count 0/Kids[]>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF"
)


def png_upload(name="test.png", size=(40, 30), fmt="PNG"):
    """A real (valid) image upload of the given pixel size."""
    buffer = BytesIO()
    Image.new("RGB", size, (200, 240, 60)).save(buffer, format=fmt)
    content_type = "image/jpeg" if fmt == "JPEG" else f"image/{fmt.lower()}"
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=content_type)


def pdf_upload(name="file.pdf"):
    return SimpleUploadedFile(name, MINIMAL_PDF, content_type="application/pdf")


class TempMediaMixin:
    """Run a TestCase with its own throw-away MEDIA_ROOT (real media is never touched)."""

    @classmethod
    def setUpClass(cls):
        cls._media_dir = tempfile.mkdtemp()
        cls._media_override = override_settings(MEDIA_ROOT=cls._media_dir)
        cls._media_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._media_override.disable()
        shutil.rmtree(cls._media_dir, ignore_errors=True)


class AdminClientMixin:
    """Logs a superuser into self.client."""

    def setUp(self):
        super().setUp()
        self.admin_user = get_user_model().objects.create_superuser(
            "qa-admin", "qa-admin@example.com", "Qa-Strong-Pass-2026!"
        )
        self.client.force_login(self.admin_user)
