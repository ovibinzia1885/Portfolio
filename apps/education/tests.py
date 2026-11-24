from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.core.testing import AdminClientMixin, TempMediaMixin, pdf_upload

from .models import Education


def make_education(**extra):
    data = dict(institution_name="Daffodil International University", degree="B.Sc.",
                field_of_study="Software Engineering", start_date=date(2017, 1, 1),
                end_date=date(2021, 12, 1), passing_year=2021, cgpa=Decimal("3.75"))
    data.update(extra)
    return Education.objects.create(**data)


class EducationModelTests(TestCase):
    def test_str_duration_and_range(self):
        edu = make_education()
        self.assertEqual(str(edu), "B.Sc. - Daffodil International University")
        self.assertEqual(edu.duration, "5 yrs")
        self.assertEqual(edu.date_range, "Jan 2017 - Dec 2021")

    def test_ongoing_when_no_end_date(self):
        edu = make_education(end_date=None)
        self.assertEqual(edu.duration, "Ongoing")
        self.assertTrue(edu.date_range.endswith("Present"))

    def test_end_before_start_is_rejected(self):
        edu = Education(institution_name="X", degree="Y", field_of_study="Z",
                        start_date=date(2021, 1, 1), end_date=date(2020, 1, 1))
        with self.assertRaises(ValidationError):
            edu.full_clean()

    def test_cgpa_above_scale_is_rejected(self):
        edu = Education(institution_name="X", degree="Y", field_of_study="Z",
                        start_date=date(2021, 1, 1), cgpa=Decimal("4.50"), scale=Decimal("4.00"))
        with self.assertRaises(ValidationError):
            edu.full_clean()

    def test_ordering_by_display_order(self):
        second = make_education(display_order=2, degree="HSC")
        first = make_education(display_order=1, degree="B.Sc.")
        self.assertEqual(list(Education.objects.all()), [first, second])

    def test_shown_on_homepage(self):
        make_education()
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "Daffodil International University")
        self.assertContains(response, "3.75")


class EducationAdminTests(TempMediaMixin, AdminClientMixin, TestCase):
    def form_data(self, **extra):
        data = {"institution_name": "Test University", "degree": "M.Sc.", "field_of_study": "SE",
                "start_date": "2022-01-01", "end_date": "2023-12-01", "scale": "4.00",
                "display_order": "0"}
        data.update(extra)
        return data

    def test_changelist_and_search(self):
        make_education()
        url = reverse("admin:education_education_changelist")
        self.assertContains(self.client.get(url), "Daffodil")
        self.assertNotContains(self.client.get(url, {"q": "nomatch"}), "Daffodil International")

    def test_add_with_certificate_update_delete(self):
        response = self.client.post(reverse("admin:education_education_add"),
                                    self.form_data(certificate=pdf_upload("cert.pdf")))
        self.assertEqual(response.status_code, 302)
        edu = Education.objects.get(institution_name="Test University")
        self.assertTrue(edu.certificate.name.endswith(".pdf"))

        change = reverse("admin:education_education_change", args=[edu.pk])
        self.assertEqual(self.client.get(change).status_code, 200)
        self.client.post(change, self.form_data(degree="MSc (updated)"))
        edu.refresh_from_db()
        self.assertEqual(edu.degree, "MSc (updated)")

        self.client.post(reverse("admin:education_education_delete", args=[edu.pk]), {"post": "yes"})
        self.assertFalse(Education.objects.exists())

    def test_rejects_disallowed_file_type(self):
        bad = SimpleUploadedFile("cert.exe", b"MZ...", content_type="application/octet-stream")
        response = self.client.post(reverse("admin:education_education_add"), self.form_data(certificate=bad))
        self.assertEqual(response.status_code, 200)  # form re-rendered with an error
        self.assertFalse(Education.objects.exists())

    def test_rejects_end_before_start(self):
        self.client.post(reverse("admin:education_education_add"),
                         self.form_data(start_date="2024-01-01", end_date="2023-01-01"))
        self.assertFalse(Education.objects.exists())
