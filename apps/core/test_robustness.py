"""Regression tests for the final QA bug report (BUG-01 … BUG-16): data changes must never break the site,
and the visible wording must come from the admin."""

import os
from datetime import date, timedelta

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.achievements.models import Achievement
from apps.blogs.models import BlogCategory, BlogPost
from apps.projects.models import Project
from apps.research.models import Research
from apps.skills.models import Skill, SkillSubcategory
from apps.training.models import Training

from .models import Profile, SiteSection
from .templatetags.portfolio_extras import highlight_author
from .testing import AdminClientMixin, TempMediaMixin, pdf_upload, png_upload
from .views import cv_filename, group_skills


class RobustnessTests(TempMediaMixin, TestCase):
    def setUp(self):
        cache.clear()
        self.profile = Profile.objects.create(full_name="Nazmul Hoque Ovy", bio="Tester.",
                                              resume=pdf_upload("cv.pdf"), photo=png_upload("me.png"))

    def remove_cv_file(self):
        os.remove(self.profile.resume.path)

    def home(self):
        return self.client.get(reverse("core:home")).content.decode()

    # BUG-01
    def test_record_with_missing_file_can_still_be_validated_and_saved(self):
        self.remove_cv_file()
        profile = Profile.objects.get(pk=self.profile.pk)
        profile.headline = "New headline"
        profile.full_clean()  # used to raise FileNotFoundError (500 in the admin)
        profile.save()

    def test_new_uploads_are_still_size_checked(self):
        from django.core.exceptions import ValidationError

        from .validators import MaxFileSizeValidator

        with self.assertRaises(ValidationError):
            MaxFileSizeValidator(max_mb=0.00001)(png_upload("big.png", size=(200, 200)))

    # BUG-02
    def test_missing_cv_file_gives_404_and_hides_buttons(self):
        self.remove_cv_file()
        for name in ("core:download_cv", "core:cv_preview", "core:cv_inline"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 404)
        self.assertNotIn("Download CV", self.home())

    def test_missing_research_pdf_gives_404(self):
        paper = Research.objects.create(title="Paper", authors="A", publication_type="journal",
                                        publication_date=date(2024, 1, 1), pdf=pdf_upload("p.pdf"))
        os.remove(paper.pdf.path)
        self.assertEqual(self.client.get(paper.get_download_url()).status_code, 404)

    def test_missing_photo_does_not_break_favicon(self):
        os.remove(self.profile.photo.path)
        self.assertEqual(self.client.get(reverse("favicon", args=[32])).status_code, 404)

    # BUG-03
    def test_availability_text_and_switch(self):
        self.profile.availability_text = "Open to freelance"
        self.profile.save()
        html = self.home()
        self.assertIn("Open to freelance", html)
        self.assertNotIn("Available for work", html)
        self.profile.is_available = False
        self.profile.save()
        self.assertNotIn("Open to freelance", self.home())

    # BUG-04 and BUG-15
    def test_section_wording_visibility_and_menu_come_from_admin(self):
        Training.objects.create(title="ISTQB prep", provider="BJIT", start_date=date(2024, 1, 1))
        section = SiteSection.objects.get(key="training")
        section.title, section.label = "Learning never stops", "Courses"
        section.save()
        html = self.home()
        self.assertIn("Learning never stops", html)
        self.assertIn('href="/#training"', html)  # menu item for the section
        self.assertIn(">Courses</a>", html)
        section.is_visible = False
        section.save()
        html = self.home()
        self.assertNotIn('id="training"', html)
        self.assertNotIn('href="/#training"', html)

    def test_page_headings_come_from_admin(self):
        SiteSection.objects.filter(key="contact").update(page_title="Say hello")
        cache.clear()
        self.assertContains(self.client.get(reverse("contact:contact")), "Say hello")

    def test_admin_edit_is_visible_on_the_next_request(self):
        # no cache: even a bulk update (which sends no signal) shows up at once, on every server process
        SiteSection.objects.filter(key="about").update(title="Fresh title", label="Me")
        html = self.home()
        self.assertIn("Fresh title", html)
        self.assertIn(">Me</a>", html)

    def test_site_works_without_section_rows(self):
        SiteSection.objects.all().delete()
        html = self.home()
        self.assertIn("Who I am", html)  # default wording
        self.assertIn('href="/#about"', html)

    # BUG-07
    def test_unknown_skill_category_gets_default_icon(self):
        Skill.objects.create(name="Docker", main_category="tools")
        Skill.objects.create(name="Postman", main_category="technical")
        self.assertEqual(self.client.get(reverse("core:home")).status_code, 200)
        self.assertTrue(all(g["icon"] for g in group_skills()))

    # BUG-08
    def test_all_awards_are_shown(self):
        for i in range(8):
            Achievement.objects.create(title=f"Award {i}", date=date(2024, 1, 1))
        html = self.home()
        self.assertTrue(all(f"Award {i}" in html for i in range(8)))

    # BUG-09
    def test_empty_project_group_hidden_on_home(self):
        Project.objects.create(title="Side project", summary="s", project_type="personal", is_featured=True)
        html = self.home()
        self.assertIn("Personal Projects", html)
        self.assertNotIn("Client Projects", html)

    # BUG-10
    def test_skills_follow_their_subcategory(self):
        sub = SkillSubcategory.objects.create(name="AI-assisted Testing", main_category="technical")
        skill = Skill.objects.create(name="Claude Code", main_category="technical", subcategory=sub)
        sub.main_category = "project_management"
        sub.save()
        skill.refresh_from_db()
        self.assertEqual(skill.main_category, "project_management")

    # BUG-11
    def test_doi_link_prefix_is_removed(self):
        for raw in ("https://doi.org/10.3390/x1", "http://dx.doi.org/10.3390/x1", "doi: 10.3390/x1"):
            paper = Research.objects.create(title=f"P {raw}", authors="A", publication_type="journal",
                                            publication_date=date(2024, 1, 1), doi=raw)
            self.assertEqual(paper.doi, "10.3390/x1")

    # BUG-12
    def test_scheduled_posts_not_counted_in_sidebar(self):
        cat = BlogCategory.objects.create(name="QA")
        BlogPost.objects.create(title="Soon", content="x", status=BlogPost.Status.PUBLISHED, category=cat,
                                published_at=timezone.now() + timedelta(days=7))
        self.assertNotContains(self.client.get(reverse("blogs:list")), "QA (1)")

    # BUG-13
    def test_cv_download_name_comes_from_profile_name(self):
        self.profile.resume.name = "resume/cv_a8Xk2.pdf"
        self.assertEqual(cv_filename(self.profile), "Nazmul_Hoque_Ovy_CV.pdf")

    # BUG-14
    def test_author_highlight_matches_whole_words_only(self):
        owner = Profile(full_name="Ali")
        self.assertEqual(str(highlight_author("Alice Smith, Ali Khan", owner)),
                         "Alice Smith, <strong>Ali</strong> Khan")

    # BUG-16
    def test_award_certificate_can_be_pdf(self):
        award = Achievement(title="Best Performer", date=date(2024, 1, 1), certificate=pdf_upload("cert.pdf"))
        award.full_clean()
        award.save()
        self.assertIn('data-cert-type="pdf"', self.home())


class SingleProfileAdminTests(AdminClientMixin, TestCase):
    # BUG-06
    def test_second_profile_cannot_be_added(self):
        add_url = reverse("admin:core_profile_add")
        self.assertEqual(self.client.get(add_url).status_code, 200)
        Profile.objects.create(full_name="Owner")
        self.assertEqual(self.client.get(add_url).status_code, 403)

    def test_site_sections_admin_edit_only(self):
        self.assertEqual(SiteSection.objects.count(), 11)
        self.assertEqual(self.client.get(reverse("admin:core_sitesection_changelist")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:core_sitesection_add")).status_code, 403)
        section = SiteSection.objects.get(key="about")
        self.assertEqual(self.client.get(reverse("admin:core_sitesection_change", args=[section.pk])).status_code, 200)
