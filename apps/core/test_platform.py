"""Day 3: admin coverage, SEO, security settings, upload validation, performance budgets."""

import os
import subprocess
import sys
from datetime import date

from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.blogs.models import BlogPost
from apps.certifications.models import Certification
from apps.core.models import Profile
from apps.core.testing import AdminClientMixin, TempMediaMixin, pdf_upload, png_upload
from apps.core.validators import MaxFileSizeValidator
from apps.projects.models import Project
from apps.research.models import Research


class AdminCoverageTests(AdminClientMixin, TestCase):
    def test_every_registered_model_has_working_admin_pages(self):
        for model, model_admin in admin.site._registry.items():
            info = (model._meta.app_label, model._meta.model_name)
            with self.subTest(model=model.__name__):
                changelist = reverse("admin:%s_%s_changelist" % info)
                self.assertEqual(self.client.get(changelist).status_code, 200)
                if model_admin.search_fields:
                    self.assertEqual(self.client.get(changelist, {"q": "test"}).status_code, 200)
                expected_add = 200 if model_admin.has_add_permission(type("R", (), {"user": self.admin_user})()) else 403
                self.assertEqual(self.client.get(reverse("admin:%s_%s_add" % info)).status_code, expected_add)

    def test_all_local_models_registered(self):
        local = [m for m in apps.get_models() if m.__module__.startswith("apps.")]
        inline_only = {"ProjectImage"}
        missing = [m.__name__ for m in local if m not in admin.site._registry and m.__name__ not in inline_only]
        self.assertEqual(missing, [])


class AdminSecurityTests(TestCase):
    def test_anonymous_redirected_to_login(self):
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response["Location"])

    def test_non_staff_user_cannot_enter(self):
        from django.contrib.auth import get_user_model

        user = get_user_model().objects.create_user("visitor", password="Visitor-Pass-2026!")
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 302)

    def test_wrong_password_rejected(self):
        from django.contrib.auth import get_user_model

        get_user_model().objects.create_superuser("boss", "b@example.com", "Right-Pass-2026!")
        response = self.client.post(reverse("admin:login"), {"username": "boss", "password": "wrong"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)


@override_settings(MAX_UPLOAD_MB=1)
class UploadValidationTests(TempMediaMixin, TestCase):
    def test_size_limit(self):
        big = SimpleUploadedFile("big.pdf", b"0" * (1024 * 1024 + 1))
        with self.assertRaises(ValidationError):
            MaxFileSizeValidator()(big)
        MaxFileSizeValidator()(SimpleUploadedFile("ok.pdf", b"0" * 1024))

    def test_extension_rules_per_field(self):
        cert = Certification(name="C", issuing_organization="O",
                             certificate=SimpleUploadedFile("c.svg", b"<svg/>"))
        with self.assertRaises(ValidationError):
            cert.full_clean()
        profile = Profile(full_name="P", resume=SimpleUploadedFile("cv.html", b"<html>"))
        with self.assertRaises(ValidationError):
            profile.full_clean()
        Profile(full_name="P", resume=pdf_upload("cv.pdf")).full_clean()
        Profile(full_name="P", photo=png_upload("me.png")).full_clean()

    def test_certificate_without_date_renders(self):
        Certification.objects.create(name="ISTQB CTFL", issuing_organization="ISTQB")
        response = self.client.get(reverse("certifications:list"))
        self.assertContains(response, "ISTQB CTFL")
        self.assertNotContains(response, "Issued")


class SeoTests(TempMediaMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        Profile.objects.create(full_name="Nazmul Hoque Ovy", headline="SQA Engineer",
                               short_intro="ISTQB-certified SQA Engineer.")
        cls.project = Project.objects.create(title="PDM Enterprise", summary="ERP automation")
        cls.post = BlogPost.objects.create(title="Hello", content="x", status=BlogPost.Status.PUBLISHED)
        cls.draft = BlogPost.objects.create(title="Secret draft", content="x")
        cls.paper = Research.objects.create(title="Paper One", authors="A")

    def test_home_meta_tags(self):
        response = self.client.get(reverse("core:home"))
        for snippet in (
            "<title>Nazmul Hoque Ovy | SQA Engineer</title>",
            '<meta name="description" content="ISTQB-certified SQA Engineer.">',
            '<link rel="canonical" href="http://testserver/">',
            '<meta property="og:title" content="Nazmul Hoque Ovy">',
            '<meta property="og:url" content="http://testserver/">',
            '<meta name="robots" content="index, follow">',
        ):
            self.assertContains(response, snippet, html=False)

    def test_canonical_drops_query_strings(self):
        response = self.client.get(reverse("projects:list"), {"utm_source": "x"})
        self.assertContains(response, '<link rel="canonical" href="http://testserver/projects/">', html=False)

    def test_detail_pages_have_unique_titles_and_descriptions(self):
        response = self.client.get(self.project.get_absolute_url())
        self.assertContains(response, "<title>PDM Enterprise | Nazmul Hoque Ovy</title>", html=False)
        self.assertContains(response, '<meta property="og:description" content="ERP automation">', html=False)

    def test_sitemap(self):
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        for url in ("http://testserver/", self.project.get_absolute_url(), self.post.get_absolute_url(),
                    self.paper.get_absolute_url(), "/certifications/"):
            self.assertIn(url, body)
        self.assertNotIn(self.draft.slug, body)
        self.assertNotIn(settings.ADMIN_URL, body)

    def test_robots_txt(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertContains(response, "Sitemap: http://testserver/sitemap.xml")
        self.assertNotContains(response, settings.ADMIN_URL.strip("/") + "/")  # admin path not advertised

    def test_404_is_noindex(self):
        response = self.client.get("/no-such-page/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "noindex", status_code=404)


class SecurityHeaderTests(TestCase):
    def test_default_security_headers(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response["X-Frame-Options"], "SAMEORIGIN")
        self.assertEqual(response["Referrer-Policy"], "strict-origin-when-cross-origin")

    def test_csrf_token_in_contact_form(self):
        self.assertContains(self.client.get(reverse("contact:contact")), "csrfmiddlewaretoken")

    def test_production_settings_require_strong_secret(self):
        """Import settings in a subprocess with DEBUG=False and a weak key -> must refuse to start."""
        env = {**os.environ, "DEBUG": "False", "SECRET_KEY": "change-me"}
        code = "import django, os; os.environ['DJANGO_SETTINGS_MODULE']='config.settings'; django.setup()"
        result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True,
                                cwd=settings.BASE_DIR)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SECRET_KEY", result.stderr)

    def test_production_settings_enable_https(self):
        env = {**os.environ, "DEBUG": "False", "SECRET_KEY": "x" * 60}
        code = (
            "import django, os; os.environ['DJANGO_SETTINGS_MODULE']='config.settings'; django.setup();"
            "from django.conf import settings as s;"
            "print(s.SECURE_SSL_REDIRECT, s.SESSION_COOKIE_SECURE, s.CSRF_COOKIE_SECURE, s.SECURE_HSTS_SECONDS > 0)"
        )
        result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True,
                                cwd=settings.BASE_DIR)
        self.assertEqual(result.stdout.strip(), "True True True True", result.stderr)


class PerformanceBudgetTests(TempMediaMixin, TestCase):
    """Query counts must not grow with the amount of content (no N+1)."""

    def make_content(self, n):
        for i in range(n):
            project = Project.objects.create(title=f"P{i}-{n}", summary="s", is_featured=True,
                                              technologies="A, B")
            project.images.create(image=png_upload(f"p{i}.png"))
            BlogPost.objects.create(title=f"B{i}-{n}", content="x", status=BlogPost.Status.PUBLISHED)
            Certification.objects.create(name=f"C{i}-{n}", issuing_organization="O", issue_date=date(2024, 1, 1))

    def count(self, url):
        with CaptureQueriesContext(connection) as ctx:
            self.assertEqual(self.client.get(url).status_code, 200)
        return len(ctx.captured_queries)

    def test_query_count_is_constant(self):
        static_urls = [reverse("core:home"), reverse("projects:list"), reverse("blogs:list"),
                       reverse("certifications:list"), "/sitemap.xml"]
        self.make_content(2)
        small = {u: self.count(u) for u in static_urls}
        small["blog detail"] = self.count(BlogPost.objects.first().get_absolute_url())
        small["project detail"] = self.count(Project.objects.first().get_absolute_url())
        self.make_content(5)
        large = {u: self.count(u) for u in static_urls}
        large["blog detail"] = self.count(BlogPost.objects.first().get_absolute_url())
        large["project detail"] = self.count(Project.objects.first().get_absolute_url())
        self.assertEqual(small, large)
        self.assertLessEqual(large[reverse("core:home")], 20)
