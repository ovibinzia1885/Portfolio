"""Read-side helpers: numbers for the footer and the admin dashboard."""

from datetime import timedelta

from django.core.cache import cache
from django.db.models import Count, Sum
from django.utils import timezone

from .middleware import TOTAL_CACHE_KEY, VIEWS_CACHE_KEY
from .models import CvDownloadStat, DailyVisitor, PageViewStat


def total_visitors():
    """All-time visitors (unique per day), cached for 5 minutes."""
    return cache.get_or_set(TOTAL_CACHE_KEY, DailyVisitor.objects.count, 300)


def _sum_views():
    return PageViewStat.objects.aggregate(s=Sum("views"))["s"] or 0


def total_views():
    """All-time page views (every counted page load), cached until the next view."""
    return cache.get_or_set(VIEWS_CACHE_KEY, _sum_views, 300)


def dashboard_stats(days=14):
    today = timezone.localdate()
    since_7, since_30 = today - timedelta(days=6), today - timedelta(days=29)
    first_day = today - timedelta(days=days - 1)

    per_day = {
        row["date"]: row
        for row in DailyVisitor.objects.filter(date__gte=first_day)
        .values("date").annotate(visitors=Count("id"), views=Sum("views"))
    }
    peak = max((row["visitors"] for row in per_day.values()), default=0) or 1
    chart = []
    for offset in range(days - 1, -1, -1):
        day = today - timedelta(days=offset)
        row = per_day.get(day, {"visitors": 0, "views": 0})
        chart.append({"date": day, "visitors": row["visitors"], "views": row["views"],
                      "pct": round(row["visitors"] * 100 / peak)})

    top_pages = (
        PageViewStat.objects.filter(date__gte=since_30)
        .values("path").annotate(total=Sum("views")).order_by("-total")[:6]
    )
    top_referrers = (
        DailyVisitor.objects.filter(date__gte=since_30).exclude(referrer="")
        .values("referrer").annotate(total=Count("id")).order_by("-total")[:5]
    )
    visitors = DailyVisitor.objects
    return {
        "today": visitors.filter(date=today).count(),
        "last_7": visitors.filter(date__gte=since_7).count(),
        "last_30": visitors.filter(date__gte=since_30).count(),
        "total": visitors.count(),
        "page_views_30": PageViewStat.objects.filter(date__gte=since_30).aggregate(s=Sum("views"))["s"] or 0,
        "page_views_total": _sum_views(),
        "cv_downloads": CvDownloadStat.objects.aggregate(s=Sum("downloads"))["s"] or 0,
        "cv_downloads_30": CvDownloadStat.objects.filter(date__gte=since_30).aggregate(s=Sum("downloads"))["s"] or 0,
        "chart": chart,
        "top_pages": list(top_pages),
        "top_referrers": list(top_referrers),
    }
