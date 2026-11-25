"""Deployment pieces: Cloudinary media storage (SDK mocked, no network) and backup/restore."""

import io
import json
import zipfile
from pathlib import Path
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.core.management import CommandError, call_command
from django.test import SimpleTestCase, TestCase, TransactionTestCase

from apps.certifications.models import Certification

from .models import Profile, SiteSection
from .storage import CloudinaryStorage, parse_cloudinary_url
from .testing import TempMediaMixin, pdf_upload, png_upload

URL = "cloudinary://123456:secret-abc@demo-cloud"


class CloudinaryStorageTests(SimpleTestCase):
    def setUp(self):
        self.storage = CloudinaryStorage(URL)

    def test_parse_url(self):
        self.assertEqual(parse_cloudinary_url(URL), {"cloud_name": "demo-cloud", "api_key": "123456",
                                                     "api_secret": "secret-abc", "secure": True})
        with self.assertRaises(ImproperlyConfigured):
            parse_cloudinary_url("https://example.com")

    def test_images_and_documents_map_to_the_right_resource(self):
        self.assertEqual(CloudinaryStorage._split("profile/me.JPG"), ("portfolio/profile/me", "image", "jpg"))
        self.assertEqual(CloudinaryStorage._split("resume/cv.pdf"), ("portfolio/resume/cv.pdf", "raw", None))

    def test_urls(self):
        image = self.storage.url("profile/me.jpg")
        pdf = self.storage.url("resume/cv.pdf")
        self.assertTrue(image.startswith("https://res.cloudinary.com/demo-cloud/image/upload/"))
        self.assertTrue(image.endswith("portfolio/profile/me.jpg"))
        self.assertTrue(pdf.startswith("https://res.cloudinary.com/demo-cloud/raw/upload/"))
        self.assertTrue(pdf.endswith("portfolio/resume/cv.pdf"))

    def test_save_keeps_the_name_and_uploads_with_public_id(self):
        with mock.patch("cloudinary.uploader.upload") as upload, \
                mock.patch("cloudinary.api.resource", side_effect=__import__("cloudinary").exceptions.NotFound):
            name = self.storage.save("resume/cv.pdf", ContentFile(b"%PDF-1.4"))
        self.assertEqual(name, "resume/cv.pdf")
        kwargs = upload.call_args.kwargs
        self.assertEqual((kwargs["public_id"], kwargs["resource_type"]), ("portfolio/resume/cv.pdf", "raw"))

    def test_exists_size_delete(self):
        with mock.patch("cloudinary.api.resource", return_value={"bytes": 2048}):
            self.assertTrue(self.storage.exists("profile/me.png"))
            self.assertEqual(self.storage.size("profile/me.png"), 2048)
        with mock.patch("cloudinary.uploader.destroy") as destroy:
            self.storage.delete("profile/me.png")
        destroy.assert_called_once_with("portfolio/profile/me", resource_type="image", invalidate=True)

    def test_malformed_cloudinary_url_stops_start_up(self):
        import os
        import subprocess
        import sys

        from django.conf import settings

        code = "import django, os; os.environ['DJANGO_SETTINGS_MODULE']='config.settings'; django.setup()"
        for bad in ("cloudinary://only-a-key", "https://example.com/x"):
            result = subprocess.run([sys.executable, "-c", code], env={**os.environ, "CLOUDINARY_URL": bad},
                                    capture_output=True, text=True, cwd=settings.BASE_DIR)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("CLOUDINARY_URL is malformed", result.stderr)

    def test_common_paste_mistakes_are_cleaned(self):
        from config.settings import normalize_cloudinary_url

        expected = "cloudinary://1111:ab_cd-9@demo"
        for pasted in ("//<1111>:<ab_cd-9>@demo", "CLOUDINARY_URL=cloudinary://1111:ab_cd-9@demo",
                       "cloudinary://<1111>:<ab_cd-9>@demo", " 'cloudinary://1111:ab_cd-9@demo' ",
                       "1111:ab_cd-9@demo", expected):
            self.assertEqual(normalize_cloudinary_url(pasted), expected, pasted)

    def test_settings_pick_cloudinary_only_when_configured(self):
        from django.conf import settings

        self.assertEqual(settings.STORAGES["default"]["BACKEND"],
                         "django.core.files.storage.FileSystemStorage")  # tests run without CLOUDINARY_URL


class BackupRestoreTests(TempMediaMixin, TestCase):
    def setUp(self):
        Profile.objects.create(full_name="Ovy", resume=pdf_upload("cv.pdf"), photo=png_upload("me.png"))
        Certification.objects.create(name="ISTQB", issuing_organization="ISTQB", certificate=pdf_upload("istqb.pdf"))

    def backup(self, tmp):
        path = Path(tmp) / "backup.zip"
        call_command("backup_site", output=str(path), stdout=io.StringIO())
        return path

    def test_backup_contains_database_and_every_file(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(self.backup(tmp)) as archive:
                names = archive.namelist()
                data = json.loads(archive.read("data.json"))
        models = {row["model"] for row in data}
        self.assertTrue({"core.profile", "certifications.certification", "core.sitesection"} <= models)
        self.assertNotIn("contenttypes.contenttype", models)
        self.assertEqual(len([n for n in names if n.startswith("media/")]), 3)

    def test_restore_into_an_empty_site(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = self.backup(tmp)
            profile = Profile.objects.get()
            resume_name = profile.resume.name
            profile.resume.storage.delete(resume_name)  # the new site has no files yet
            Profile.objects.all().delete()
            Certification.objects.all().delete()
            call_command("restore_site", str(path), stdout=io.StringIO())
        restored = Profile.objects.get()
        self.assertEqual(restored.full_name, "Ovy")
        self.assertTrue(restored.resume.storage.exists(resume_name))
        self.assertEqual(Certification.objects.count(), 1)
        self.assertEqual(SiteSection.objects.count(), 11)

    def test_restore_refuses_to_overwrite_a_live_site(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(CommandError):
                call_command("restore_site", str(self.backup(tmp)), stdout=io.StringIO())


class RestoreReplaceTests(TempMediaMixin, TransactionTestCase):
    """Real commits (like production): restore --replace into a freshly migrated database."""

    serialized_rollback = True  # keep the migration seed rows for the other tests

    def test_restore_replace_into_a_freshly_migrated_database(self):
        import tempfile

        from apps.skills.models import SkillSubcategory

        # migration skills/0003 seeds default subcategories (incl. "Manual Testing") in every new database
        self.assertTrue(SkillSubcategory.objects.filter(name="Manual Testing").exists())
        Profile.objects.create(full_name="Ovy", resume=pdf_upload("cv.pdf"))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "backup.zip"
            call_command("backup_site", output=str(path), stdout=io.StringIO())
            # a new production database: same seed rows, but under other ids, and no profile yet
            Profile.objects.all().delete()
            for sub in SkillSubcategory.objects.all():
                SkillSubcategory.objects.filter(pk=sub.pk).update(id=sub.pk + 1000)
            with self.assertRaises(CommandError):  # plain restore collides with the seed rows
                call_command("restore_site", str(path), stdout=io.StringIO())
            call_command("restore_site", str(path), replace=True, stdout=io.StringIO())
        self.assertEqual(SkillSubcategory.objects.filter(name="Manual Testing").count(), 1)
        self.assertEqual(Profile.objects.count(), 1)
        self.assertEqual(SiteSection.objects.count(), 11)
