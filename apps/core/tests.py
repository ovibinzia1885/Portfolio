"""Day 2 functional tests: pages, dynamic content, blog, research, contact, downloads."""

import re
import shutil
import tempfile
from datetime import date, timedelta

from django.core.files.base import ContentFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.blogs.models import BlogCategory, BlogPost, BlogTag
from apps.contact.models import ContactMessage
from apps.core.management.commands.seed_demo import SAMPLE_PDF
from apps.core.models import Profile
from apps.education.models import Education
from apps.experience.models import Experience
from apps.projects.models import Project
from apps.research.models import Research

TEMP_MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA, ALLOWED_HOSTS=["testserver", "localhost"])
class SiteTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)

    # ---- pages -----------------------------------------------------------
    def test_home_renders_all_sections(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        for section_id in ("hero", "about", "education", "experience", "skills", "projects",
                           "achievements", "certifications", "training", "blogs", "research", "contact"):
            self.assertContains(response, f'id="{section_id}"')

    def test_home_empty_database_still_renders(self):
        call_command("seed_demo", "--clear", verbosity=0)
        Profile.objects.all().delete()
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No featured projects")
        self.assertContains(response, "No education added yet")

    def test_education_dynamic_fields(self):
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "Example University")
        self.assertContains(response, "B.Sc.")
        self.assertContains(response, "Department of CSE")
        self.assertContains(response, "CGPA 3.75 / 4.00")
        self.assertContains(response, "Passed 2021")
        self.assertContains(response, "4 yrs")

    def test_experience_timeline_and_current(self):
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "timeline-item reveal current")
        self.assertContains(response, "Present")
        self.assertContains(response, "https://example.com")

    def test_skills_grouped_by_category(self):
        response = self.client.get(reverse("core:home"))
        for label in ("Technical Skills", "Project Management Skills", "Soft Skills", "API Testing"):
            self.assertContains(response, label)

    def test_all_internal_links_resolve(self):
        """Crawl href/src of the main pages; every internal target must return 200."""
        pages = [reverse("core:home"), reverse("projects:list"), reverse("blogs:list"),
                 reverse("research:list"), reverse("contact:contact")]
        pages += [p.get_absolute_url() for p in Project.objects.all()]
        pages += [p.get_absolute_url() for p in BlogPost.objects.published()]
        pages += [reverse("research:detail", args=[r.pk]) for r in Research.objects.all()]
        checked = set()
        for page in pages:
            html = self.client.get(page).content.decode()
            for target in re.findall(r'(?:href|src|action)="(/[^"#]*)', html):
                if target in checked or target.startswith("//") or target.startswith("/static/"):
                    continue
                checked.add(target)
                if target.startswith("/media/"):
                    continue  # media served by the dev server only
                response = self.client.get(target)
                self.assertIn(response.status_code, (200, 302), f"{target} (linked from {page})")
        self.assertTrue(len(checked) > 10)

    # ---- projects ----------------------------------------------------------
    def test_project_list_detail_and_links(self):
        response = self.client.get(reverse("projects:list"))
        self.assertContains(response, "data-filter=")
        project = Project.objects.first()
        detail = self.client.get(project.get_absolute_url())
        self.assertContains(detail, "View on GitHub")
        self.assertContains(detail, "Live demo")
        self.assertContains(detail, "carousel" if project.images.count() > 1 else "gallery-main")

    def test_projects_split_into_client_and_personal(self):
        for url in (reverse("core:home"), reverse("projects:list")):
            response = self.client.get(url)
            groups = {g["key"]: g for g in response.context["project_groups"]}
            self.assertEqual(set(groups), {"client", "personal"})
            self.assertTrue(all(p.project_type == "client" for p in groups["client"]["projects"]))
            self.assertTrue(all(p.project_type == "personal" for p in groups["personal"]["projects"]))
            self.assertContains(response, "Client Projects")
            self.assertContains(response, "Personal Projects")
        # list page shows every project; home shows only featured ones
        all_groups = self.client.get(reverse("projects:list")).context["project_groups"]
        self.assertEqual(sum(len(g["projects"]) for g in all_groups), Project.objects.count())
        home_groups = self.client.get(reverse("core:home")).context["project_groups"]
        self.assertEqual(sum(len(g["projects"]) for g in home_groups), Project.objects.filter(is_featured=True).count())

    def test_empty_group_shows_message(self):
        Project.objects.filter(project_type="personal").delete()
        response = self.client.get(reverse("projects:list"))
        self.assertContains(response, "No projects in this group yet.")

    def test_project_unknown_slug_404(self):
        self.assertEqual(self.client.get("/projects/nope/").status_code, 404)

    def test_unicode_title_gets_valid_slug(self):
        project = Project.objects.create(title="প্রকল্প", summary="x")
        self.assertTrue(project.slug)
        self.assertEqual(self.client.get(project.get_absolute_url()).status_code, 200)

    # ---- blog --------------------------------------------------------------
    def test_blog_pagination(self):
        first = self.client.get(reverse("blogs:list"))
        self.assertEqual(first.context["page_obj"].paginator.count, 7)  # draft hidden
        self.assertEqual(len(first.context["posts"]), 6)
        second = self.client.get(reverse("blogs:list"), {"page": 2})
        self.assertEqual(len(second.context["posts"]), 1)

    def test_blog_search(self):
        response = self.client.get(reverse("blogs:list"), {"q": "Sample Article 3"})
        self.assertEqual(response.context["page_obj"].paginator.count, 1)
        self.assertEqual(self.client.get(reverse("blogs:list"), {"q": "zzzz-none"}).context["page_obj"].paginator.count, 0)

    def test_blog_category_and_tag_filters(self):
        category = BlogCategory.objects.first()
        response = self.client.get(category.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(all(p.category_id == category.pk for p in response.context["posts"]))
        tag = BlogTag.objects.first()
        response = self.client.get(tag.get_absolute_url())
        self.assertTrue(all(tag in p.tags.all() for p in response.context["posts"]))

    def test_blog_draft_is_not_public(self):
        draft = BlogPost.objects.get(status="draft")
        self.assertEqual(self.client.get(draft.get_absolute_url()).status_code, 404)

    def test_blog_future_post_hidden(self):
        post = BlogPost.objects.create(title="Future", content="x", status="published",
                                       published_at=timezone.now() + timedelta(days=3))
        self.assertEqual(self.client.get(post.get_absolute_url()).status_code, 404)

    def test_blog_detail(self):
        post = BlogPost.objects.published().first()
        response = self.client.get(post.get_absolute_url())
        self.assertContains(response, post.title)
        self.assertContains(response, "min read")

    # ---- research ----------------------------------------------------------
    def test_research_list_filter_detail_download(self):
        self.assertEqual(self.client.get(reverse("research:list")).context["page_obj"].paginator.count, 3)
        filtered = self.client.get(reverse("research:list"), {"type": "thesis"})
        self.assertEqual(filtered.context["page_obj"].paginator.count, 1)
        paper = Research.objects.first()
        detail = self.client.get(reverse("research:detail", args=[paper.pk]))
        self.assertContains(detail, "Abstract")
        self.assertContains(detail, "https://doi.org/10.0000/sample")
        pdf = self.client.get(reverse("research:download", args=[paper.pk]))
        self.assertEqual(pdf.status_code, 200)
        self.assertIn("attachment", pdf["Content-Disposition"])
        self.assertTrue(b"".join(pdf.streaming_content).startswith(b"%PDF"))

    def test_research_without_pdf_download_404(self):
        paper = Research.objects.create(title="No pdf", authors="A")
        self.assertEqual(self.client.get(reverse("research:download", args=[paper.pk])).status_code, 404)

    # ---- CV ----------------------------------------------------------------
    def test_cv_download(self):
        response = self.client.get(reverse("core:download_cv"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("attachment", response["Content-Disposition"])

    def test_cv_missing_404(self):
        Profile.objects.update(resume="")
        self.assertEqual(self.client.get(reverse("core:download_cv")).status_code, 404)

    # ---- contact -----------------------------------------------------------
    VALID = {"name": "Jane Doe", "email": "jane@example.com", "subject": "Hello",
             "message": "This is a valid message body."}

    def test_contact_success_saves_and_shows_message(self):
        response = self.client.post(reverse("contact:contact"), self.VALID, follow=True)
        self.assertEqual(ContactMessage.objects.count(), 1)
        self.assertContains(response, "Your message has been sent")
        self.assertContains(response, "toast-p success")

    def test_contact_validation_errors(self):
        bad = {**self.VALID, "email": "not-an-email", "message": "short"}
        response = self.client.post(reverse("contact:contact"), bad)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)
        self.assertContains(response, "Enter a valid email address")
        self.assertContains(response, "at least 10 characters")
        self.assertContains(response, "toast-p error")

    def test_contact_required_fields(self):
        response = self.client.post(reverse("contact:contact"), {})
        self.assertContains(response, "This field is required")
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_contact_honeypot_not_stored(self):
        response = self.client.post(reverse("contact:contact"), {**self.VALID, "website": "http://spam"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_contact_csrf_enforced(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(reverse("contact:contact"), self.VALID).status_code, 403)

    # ---- admin sanity ------------------------------------------------------
    def test_404_page_uses_template(self):
        response = self.client.get("/does-not-exist/")
        self.assertEqual(response.status_code, 404)
