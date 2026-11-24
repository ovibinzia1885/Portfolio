from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.core.models import Profile

from .models import DailyVisitor, PageViewStat
from .stats import dashboard_stats

CHROME = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
FIREFOX = "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0"


class VisitorCountingTests(TestCase):
    def setUp(self):
        cache.clear()

    def visit(self, url="/", agent=CHROME, ip="203.0.113.7", **extra):
        return self.client.get(url, HTTP_USER_AGENT=agent, REMOTE_ADDR=ip, **extra)

    def test_same_visitor_counts_once_per_day_but_views_add_up(self):
        self.visit("/")
        self.visit("/projects/")
        self.visit("/")
        self.assertEqual(DailyVisitor.objects.count(), 1)
        visitor = DailyVisitor.objects.get()
        self.assertEqual(visitor.views, 3)
        self.assertEqual(visitor.first_page, "/")
        self.assertEqual(PageViewStat.objects.get(path="/").views, 2)
        self.assertEqual(PageViewStat.objects.get(path="/projects/").views, 1)

    def test_different_people_are_different_visitors(self):
        self.visit(agent=CHROME, ip="203.0.113.7")
        self.visit(agent=FIREFOX, ip="203.0.113.7")
        self.visit(agent=CHROME, ip="198.51.100.20")
        self.assertEqual(DailyVisitor.objects.count(), 3)

    def test_ip_and_browser_are_not_stored(self):
        self.visit(ip="203.0.113.7")
        visitor = DailyVisitor.objects.get()
        stored = " ".join(str(v) for v in DailyVisitor.objects.values().get().values())
        self.assertNotIn("203.0.113.7", stored)
        self.assertNotIn("Chrome", stored)
        self.assertEqual(len(visitor.visitor), 64)

    def test_not_counted_bots_admin_static_errors_and_no_agent(self):
        self.visit(agent="Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)")
        self.visit(agent="facebookexternalhit/1.1")
        self.visit(agent="")
        self.visit("/admin/login/")
        self.visit("/robots.txt")
        self.visit("/sitemap.xml")
        self.visit("/this-page-does-not-exist/")
        self.client.post(reverse("contact:contact"), {}, HTTP_USER_AGENT=CHROME)
        self.visit("/", HTTP_SEC_PURPOSE="prefetch")
        self.assertEqual(DailyVisitor.objects.count(), 0)
        self.assertEqual(PageViewStat.objects.count(), 0)

    def test_site_owner_is_not_counted(self):
        staff = get_user_model().objects.create_user("owner", password="Owner-Pass-2026!", is_staff=True)
        self.client.force_login(staff)
        self.visit("/")
        self.assertEqual(DailyVisitor.objects.count(), 0)

    def test_referrer_domain_only(self):
        self.visit("/", HTTP_REFERER="https://www.linkedin.com/in/someone/?utm=1")
        self.assertEqual(DailyVisitor.objects.get().referrer, "www.linkedin.com")

    def test_footer_counter_and_toggle(self):
        profile = Profile.objects.create(full_name="Ovy")
        self.assertNotContains(self.client.get("/"), 'class="visitor-count"')  # hidden while 0
        cache.clear()
        DailyVisitor.objects.create(date=timezone.localdate() - timedelta(days=1), visitor="a" * 64, views=4)
        response = self.client.get("/")  # no user agent: not counted itself
        self.assertContains(response, 'class="visitor-count"')
        self.assertContains(response, "<strong>1</strong> visitor")
        profile.show_visitor_count = False
        profile.save()
        cache.clear()
        self.assertNotContains(self.client.get("/"), 'class="visitor-count"')

    def test_counting_errors_never_break_the_page(self):
        from unittest import mock

        with mock.patch("apps.analytics.middleware.record", side_effect=RuntimeError("db down")):
            with self.assertLogs("apps.analytics.middleware", level="ERROR"):
                response = self.visit("/")
        self.assertEqual(response.status_code, 200)


class VisitorStatsTests(TestCase):
    def test_dashboard_numbers_and_chart(self):
        today = timezone.localdate()
        for days_ago, n in ((0, 3), (1, 2), (10, 1), (40, 5)):
            for i in range(n):
                DailyVisitor.objects.create(date=today - timedelta(days=days_ago), visitor=f"{days_ago}-{i}".ljust(64, "x"),
                                            views=2, referrer="github.com" if i == 0 else "")
        PageViewStat.objects.create(date=today, path="/", views=7)
        PageViewStat.objects.create(date=today, path="/projects/", views=3)
        stats = dashboard_stats()
        self.assertEqual((stats["today"], stats["last_7"], stats["last_30"], stats["total"]), (3, 5, 6, 11))
        self.assertEqual(stats["page_views_30"], 10)
        self.assertEqual(len(stats["chart"]), 14)
        self.assertEqual(stats["chart"][-1]["visitors"], 3)
        self.assertEqual(stats["chart"][-1]["pct"], 100)
        self.assertEqual(stats["top_pages"][0]["path"], "/")
        self.assertEqual(stats["top_referrers"][0]["referrer"], "github.com")

    def test_admin_dashboard_shows_visitors_and_data_is_read_only(self):
        admin_user = get_user_model().objects.create_superuser("boss", "b@example.com", "Boss-Pass-2026!")
        self.client.force_login(admin_user)
        DailyVisitor.objects.create(date=timezone.localdate(), visitor="z" * 64, views=1)
        html = self.client.get(reverse("admin:index")).content.decode()
        self.assertIn("op-visits", html)
        self.assertIn("Last 7 days", html)
        self.assertEqual(self.client.get(reverse("admin:analytics_dailyvisitor_changelist")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:analytics_dailyvisitor_add")).status_code, 403)
        self.assertEqual(DailyVisitor.objects.count(), 1)  # admin pages are never counted
