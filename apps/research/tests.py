from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.core.testing import AdminClientMixin, TempMediaMixin, pdf_upload

from .models import Research


class ResearchModelUrlTests(TempMediaMixin, TestCase):
    def test_slug_and_urls(self):
        paper = Research.objects.create(title="AI Driven Test Optimisation", authors="N. H. Ovy")
        self.assertEqual(paper.slug, "ai-driven-test-optimisation")
        self.assertEqual(paper.get_absolute_url(), "/research/ai-driven-test-optimisation/")
        self.assertEqual(paper.get_download_url(), "/research/ai-driven-test-optimisation/download/")
        twin = Research.objects.create(title="AI Driven Test Optimisation", authors="X")
        self.assertNotEqual(paper.slug, twin.slug)

    def test_legacy_numeric_url_redirects_permanently(self):
        paper = Research.objects.create(title="Old link", authors="A")
        response = self.client.get(f"/research/{paper.pk}/")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], paper.get_absolute_url())
        self.assertEqual(self.client.get("/research/999999/").status_code, 404)

    def test_numeric_title_still_reachable(self):
        paper = Research.objects.create(title="2024", authors="A")
        self.assertEqual(self.client.get(paper.get_absolute_url()).status_code, 200)

    def test_detail_download_and_type_filter(self):
        paper = Research.objects.create(title="Thesis", authors="A", publication_type="thesis",
                                        abstract="Abstract text", pdf=pdf_upload())
        Research.objects.create(title="Journal paper", authors="B", publication_type="journal")
        detail = self.client.get(paper.get_absolute_url())
        self.assertContains(detail, "Abstract text")
        download = self.client.get(paper.get_download_url())
        self.assertEqual(download.status_code, 200)
        self.assertIn("attachment", download["Content-Disposition"])
        filtered = self.client.get(reverse("research:list"), {"type": "thesis"})
        self.assertEqual(list(filtered.context["papers"]), [paper])
        invalid = self.client.get(reverse("research:list"), {"type": "<bad>"})
        self.assertEqual(invalid.context["active_type"], "")
        self.assertEqual(len(invalid.context["papers"]), 2)


class ResearchDisplayTests(TestCase):
    def test_date_label_year_only_or_month(self):
        from datetime import date

        self.assertEqual(Research(publication_date=date(2021, 1, 1)).date_label, "2021")
        self.assertEqual(Research(publication_date=date(2024, 2, 7)).date_label, "Feb 2024")
        self.assertEqual(Research(publication_date=None).date_label, "")

    def test_long_title_slug_cut_at_word_boundary(self):
        paper = Research.objects.create(
            title="Exploring Machine Learning for Predicting Cerebral Stroke: A Study in Discovery", authors="A")
        self.assertLessEqual(len(paper.slug), 60)
        self.assertFalse(paper.slug.endswith("-"))
        self.assertTrue("exploring-machine-learning-for-predicting-cerebral-stroke-a".startswith(paper.slug))

    def test_indexing_badge_and_owner_highlight(self):
        from apps.core.models import Profile

        Profile.objects.create(full_name="Nazmul Hoque Ovy")
        Research.objects.create(title="Q2 paper", authors="R Mia, Nazmul Hoque Ovy, <script>x</script>",
                                indexing="Q2")
        response = self.client.get(reverse("research:list"))
        self.assertContains(response, "<strong>Nazmul Hoque Ovy</strong>", html=False)
        self.assertContains(response, "Q2")
        self.assertNotContains(response, "<script>x</script>")  # author text stays escaped

    def test_display_order_controls_listing(self):
        second = Research.objects.create(title="B", authors="A", display_order=2)
        first = Research.objects.create(title="A", authors="A", display_order=1)
        response = self.client.get(reverse("research:list"))
        self.assertEqual(list(response.context["papers"]), [first, second])


class ResearchAdminTests(TempMediaMixin, AdminClientMixin, TestCase):
    def data(self, **extra):
        values = {"title": "Admin paper", "slug": "", "authors": "A", "publication_type": "journal",
                  "display_order": "0"}
        values.update(extra)
        return values

    def test_add_with_pdf_and_delete(self):
        response = self.client.post(reverse("admin:research_research_add"), self.data(pdf=pdf_upload()))
        self.assertEqual(response.status_code, 302)
        paper = Research.objects.get()
        self.assertTrue(paper.pdf.name.endswith(".pdf"))
        self.assertContains(self.client.get(reverse("admin:research_research_changelist"), {"q": "Admin"}),
                            "Admin paper")
        self.client.post(reverse("admin:research_research_delete", args=[paper.pk]), {"post": "yes"})
        self.assertFalse(Research.objects.exists())

    def test_non_pdf_rejected(self):
        bad = SimpleUploadedFile("paper.html", b"<script></script>", content_type="text/html")
        response = self.client.post(reverse("admin:research_research_add"), self.data(pdf=bad))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Research.objects.exists())
