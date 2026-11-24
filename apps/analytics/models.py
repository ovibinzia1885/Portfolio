"""Privacy-friendly visitor counting.

No IP address, cookie or user agent is stored. A visitor is identified per day by a one-way hash
of (secret key + date + IP + browser), so the same person counts once per day and cannot be traced.
"""

from django.db import models


class DailyVisitor(models.Model):
    """One row per unique visitor per day."""

    date = models.DateField(db_index=True)
    visitor = models.CharField(max_length=64, help_text="Anonymous daily hash (not reversible).")
    views = models.PositiveIntegerField(default=0)
    first_page = models.CharField(max_length=300, blank=True)
    referrer = models.CharField(max_length=200, blank=True, help_text="Website the visitor came from (domain only).")
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-last_seen"]
        constraints = [models.UniqueConstraint(fields=["date", "visitor"], name="unique_daily_visitor")]
        verbose_name = "daily visitor"

    def __str__(self):
        return f"{self.date} · {self.visitor[:10]}…"


class PageViewStat(models.Model):
    """Page views per page per day."""

    date = models.DateField(db_index=True)
    path = models.CharField(max_length=300)
    views = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-date", "-views"]
        constraints = [models.UniqueConstraint(fields=["date", "path"], name="unique_daily_page")]
        verbose_name = "page view (daily)"
        verbose_name_plural = "page views (daily)"

    def __str__(self):
        return f"{self.date} {self.path} ({self.views})"
