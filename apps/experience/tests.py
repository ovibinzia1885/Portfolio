from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.core.testing import AdminClientMixin, TempMediaMixin, png_upload

from .models import Experience


def make_experience(**extra):
    data = dict(company="BJIT Limited", company_url="https://bjitgroup.com/", designation="SQA Engineer",
                start_date=date(2022, 4, 1), end_date=date(2025, 8, 1),
                responsibilities="Line one\nLine two", technologies="Playwright, SQL , ,Jira")
    data.update(extra)
    return Experience.objects.create(**data)


class ExperienceModelTests(TestCase):
    def test_duration_range_and_technologies(self):
        exp = make_experience()
        self.assertEqual(exp.duration, "3 yrs 5 mos")
        self.assertEqual(exp.date_range, "Apr 2022 - Aug 2025")
        self.assertEqual(exp.technology_list, ["Playwright", "SQL", "Jira"])

    def test_current_job_shows_present_and_clears_end_date(self):
        exp = Experience(company="A", designation="B", start_date=date(2024, 1, 1),
                         end_date=date(2024, 6, 1), is_current=True)
        exp.full_clean()
        self.assertIsNone(exp.end_date)
        self.assertTrue(exp.date_range.endswith("Present"))

    def test_validation_rules(self):
        missing_end = Experience(company="A", designation="B", start_date=date(2024, 1, 1))
        with self.assertRaises(ValidationError):
            missing_end.full_clean()
        reversed_dates = Experience(company="A", designation="B", start_date=date(2024, 1, 1),
                                    end_date=date(2023, 1, 1))
        with self.assertRaises(ValidationError):
            reversed_dates.full_clean()

    def test_homepage_timeline_with_company_link(self):
        make_experience()
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "BJIT Limited")
        self.assertContains(response, "https://bjitgroup.com/")
        self.assertContains(response, "Line two")


class ExperienceAdminTests(TempMediaMixin, AdminClientMixin, TestCase):
    def test_add_with_logo_search_and_delete(self):
        data = {"company": "Acme", "designation": "QA", "employment_type": "full_time",
                "start_date": "2020-01-01", "end_date": "2021-01-01", "display_order": "0",
                "company_logo": png_upload("logo.png")}
        response = self.client.post(reverse("admin:experience_experience_add"), data)
        self.assertEqual(response.status_code, 302)
        exp = Experience.objects.get(company="Acme")
        self.assertTrue(exp.company_logo)

        changelist = reverse("admin:experience_experience_changelist")
        self.assertContains(self.client.get(changelist, {"q": "Acme"}), "Acme")
        self.assertContains(self.client.get(changelist, {"employment_type__exact": "full_time"}), "Acme")

        self.client.post(reverse("admin:experience_experience_delete", args=[exp.pk]), {"post": "yes"})
        self.assertFalse(Experience.objects.exists())

    def test_fake_image_rejected(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        fake = SimpleUploadedFile("logo.png", b"not an image", content_type="image/png")
        data = {"company": "Acme", "designation": "QA", "employment_type": "full_time",
                "start_date": "2020-01-01", "is_current": "on", "display_order": "0", "company_logo": fake}
        response = self.client.post(reverse("admin:experience_experience_add"), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Experience.objects.exists())
