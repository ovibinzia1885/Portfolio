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
        self.assertEqual(pdf, "/files/resume/cv.pdf")  # documents go through this site (signed download)
        cdn = self.storage.cdn_url("resume/cv.pdf")
        self.assertTrue(cdn.startswith("https://res.cloudinary.com/demo-cloud/raw/upload/"))
        self.assertTrue(cdn.endswith("portfolio/resume/cv.pdf"))

    def test_documents_are_downloaded_with_a_signed_url(self):
        with mock.patch("urllib.request.urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value.read.return_value = b"%PDF-1.4"
            data = self.storage.open("resume/cv.pdf").read()
        self.assertEqual(data, b"%PDF-1.4")
        source = urlopen.call_args.args[0]
        self.assertIn("api.cloudinary.com", source)  # private download API, not the public CDN
        self.assertIn("signature=", source)

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

    def test_malformed_cloudinary_url_keeps_the_site_up_and_logs_its_shape(self):
        import os
        import subprocess
        import sys

        from django.conf import settings

        code = ("import django, os; os.environ['DJANGO_SETTINGS_MODULE']='config.settings'; django.setup();"
                "from django.conf import settings as s; print(s.STORAGES['default']['BACKEND'].rsplit('.', 1)[-1],"
                " 'CLOUDINARY_URL' in os.environ)")
        result = subprocess.run([sys.executable, "-c", code],
                                env={**os.environ, "CLOUDINARY_URL": "https://example.com/Secret99"},
                                capture_output=True, text=True, cwd=settings.BASE_DIR)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "FileSystemStorage False")  # local storage, SDK sees no bad value
        self.assertIn("CLOUDINARY_URL is malformed", result.stderr)
        self.assertIn("xxxxx://xxxxxxx.xxx/xxxxxxxx", result.stderr)  # shape only
        self.assertNotIn("Secret99", result.stderr)

    def test_common_paste_mistakes_are_cleaned(self):
        from config.settings import normalize_cloudinary_url

        expected = "cloudinary://1111:ab_cd-9@demo"
        for pasted in ("//<1111>:<ab_cd-9>@demo", "CLOUDINARY_URL=cloudinary://1111:ab_cd-9@demo",
                       "cloudinary://<1111>:<ab_cd-9>@demo", " 'cloudinary://1111:ab_cd-9@demo' ",
                       "1111:ab_cd-9@demo", expected,
                       # the dashboard template pasted together with the key/secret lines
                       "CLOUDINARY_URL=cloudinary://<your_api_key>:<your_api_secret>@demo\n\n"
                       "API Secret:ab_cd-9\n\nAPI Key: 1111",
                       "cloudinary://<your_api_key>:<your_api_secret>@demo API Key: 1111"):
            if "API Key: 1111" in pasted and "API Secret" not in pasted:
                continue  # secret missing: covered below
            self.assertEqual(normalize_cloudinary_url(pasted), expected, pasted)
        from apps.core.cloudinary_url import is_valid

        self.assertFalse(is_valid(normalize_cloudinary_url(
            "cloudinary://<your_api_key>:<your_api_secret>@demo")))  # template: never used as credentials
        self.assertTrue(is_valid(expected))
        # placeholders without real values stay unusable (reported, never used)
        self.assertFalse(normalize_cloudinary_url("cloudinary://<your_api_key>:<your_api_secret>@demo")
                         .startswith("cloudinary://1111"))
        self.assertEqual(normalize_cloudinary_url(""), "")

    def test_admin_url_accepts_a_pasted_full_address(self):
        import os
        import subprocess
        import sys

        from django.conf import settings

        code = ("import django, os; os.environ['DJANGO_SETTINGS_MODULE']='config.settings'; django.setup();"
                "from django.conf import settings as s; print(s.ADMIN_URL)")
        for pasted in ("https://nazmulhoqueovy.onrender.com/ovy-panel-1a2b/", "/ovy-panel-1a2b", "ovy-panel-1a2b/"):
            result = subprocess.run([sys.executable, "-c", code], env={**os.environ, "ADMIN_URL": pasted},
                                    capture_output=True, text=True, cwd=settings.BASE_DIR)
            self.assertEqual(result.stdout.strip(), "ovy-panel-1a2b/", (pasted, result.stderr[-300:]))

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


class ConfiguredMediaStorageTests(TempMediaMixin, TestCase):
    """Production without a usable CLOUDINARY_URL: the connection saved in Admin > Site settings is used."""

    def setUp(self):
        from .storage import ConfiguredMediaStorage

        ConfiguredMediaStorage.reset()
        self.addCleanup(ConfiguredMediaStorage.reset)
        self.storage = ConfiguredMediaStorage()

    def test_local_files_until_a_connection_is_saved(self):
        from django.core.files.storage import FileSystemStorage

        from .models import SiteSetting
        from .storage import ConfiguredMediaStorage

        self.assertIsInstance(ConfiguredMediaStorage.target(), FileSystemStorage)
        self.assertFalse(self.storage.is_cloudinary)
        SiteSetting.objects.create(cloudinary_url="cloudinary://<your_api_key>:<your_api_secret>@demo\n"
                                                  "API Secret: s3cr3t\nAPI Key: 1111")
        self.assertTrue(self.storage.is_cloudinary)  # saved value is cleaned and used at once
        self.assertTrue(self.storage.url("profile/me.jpg").startswith("https://res.cloudinary.com/demo/image/"))

    def test_admin_form_keeps_rejects_and_cleans(self):
        from .admin import SiteSettingForm
        from .models import SiteSetting

        setting = SiteSetting.objects.create(cloudinary_url="cloudinary://1111:s3cr3t@demo")
        form = SiteSettingForm(data={"cloudinary_url": ""}, instance=setting)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.save().cloudinary_url, "cloudinary://1111:s3cr3t@demo")  # empty = keep
        bad = SiteSettingForm(data={"cloudinary_url": "hello world"}, instance=setting)
        self.assertFalse(bad.is_valid())
        self.assertNotIn("hello", str(bad.errors))  # only the masked shape is shown
        good = SiteSettingForm(data={"cloudinary_url": "//<2222>:<n3w>@demo"}, instance=setting)
        self.assertTrue(good.is_valid())
        self.assertEqual(good.save().cloudinary_url, "cloudinary://2222:n3w@demo")

    def test_set_cloudinary_command_tests_login_then_saves(self):
        from .models import SiteSetting

        with mock.patch("cloudinary.api.ping", return_value={"status": "ok"}):
            call_command("set_cloudinary", "cloudinary://1111:s3cr3t@demo", stdout=io.StringIO())
        self.assertEqual(SiteSetting.objects.get().cloudinary_url, "cloudinary://1111:s3cr3t@demo")
        with self.assertRaises(CommandError):
            call_command("set_cloudinary", "not a url", stdout=io.StringIO())

    def test_backup_never_contains_the_secret(self):
        import tempfile

        from .models import SiteSetting

        SiteSetting.objects.create(cloudinary_url="cloudinary://1111:s3cr3t@demo")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "b.zip"
            call_command("backup_site", output=str(path), stdout=io.StringIO())
            with zipfile.ZipFile(path) as archive:
                self.assertNotIn(b"s3cr3t", archive.read("data.json"))

    def test_dashboard_warns_while_not_connected(self):
        from django.test import override_settings

        from .dashboard import media_warning

        backend = {"default": {"BACKEND": "apps.core.storage.ConfiguredMediaStorage"},
                   "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}}
        with override_settings(STORAGES=backend):
            self.assertIn("Site settings", media_warning())


class MediaFileViewTests(TempMediaMixin, TestCase):
    def test_serves_documents_inline_and_blocks_tricks(self):
        cert = Certification.objects.create(name="ISTQB", issuing_organization="ISTQB",
                                            certificate=pdf_upload("istqb.pdf"))
        response = self.client.get(f"/files/{cert.certificate.name}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("inline", response["Content-Disposition"])
        self.assertEqual(self.client.get("/files/certifications/missing.pdf").status_code, 404)
        self.assertEqual(self.client.get("/files/../settings.py").status_code, 404)
