"""Counts real page views of the public site (see models.py for the privacy approach)."""

import hashlib
import logging
import re
from urllib.parse import urlparse

from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from .models import DailyVisitor, PageViewStat

logger = logging.getLogger(__name__)

BOT_RE = re.compile(
    r"bot|crawl|spider|slurp|bingpreview|facebookexternalhit|whatsapp|telegram|discord|preview|"
    r"headless|lighthouse|pingdom|uptime|monitor|curl|wget|python-requests|httpclient|scrapy",
    re.IGNORECASE,
)
SKIP_PREFIXES = ("/static/", "/media/", "/favicon", "/robots.txt", "/sitemap.xml", "/cv/view/")
TOTAL_CACHE_KEY = "analytics:total_visitors"


def client_ip(request):
    if getattr(settings, "TRUST_X_FORWARDED_FOR", False):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def visitor_hash(request, day):
    raw = "|".join([settings.SECRET_KEY, day.isoformat(), client_ip(request),
                    request.META.get("HTTP_USER_AGENT", "")[:300]])
    return hashlib.sha256(raw.encode()).hexdigest()


def should_count(request, response):
    if request.method != "GET" or response.status_code != 200:
        return False
    if "text/html" not in response.get("Content-Type", ""):
        return False
    path = request.path
    if path.startswith(SKIP_PREFIXES) or path.startswith("/" + settings.ADMIN_URL.lstrip("/")):
        return False
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated and user.is_staff:  # the owner browsing the site
        return False
    if request.headers.get("Purpose") == "prefetch" or request.headers.get("Sec-Purpose", "").startswith("prefetch"):
        return False
    agent = request.META.get("HTTP_USER_AGENT", "")
    return bool(agent) and not BOT_RE.search(agent)


def referrer_domain(request):
    host = urlparse(request.META.get("HTTP_REFERER", "")).netloc.lower()
    return "" if not host or host == request.get_host().lower() else host[:200]


def record(request):
    today = timezone.localdate()
    path = request.path[:300]
    with transaction.atomic():
        updated = PageViewStat.objects.filter(date=today, path=path).update(views=F("views") + 1)
        if not updated:
            try:
                with transaction.atomic():
                    PageViewStat.objects.create(date=today, path=path, views=1)
            except IntegrityError:  # created by a parallel request
                PageViewStat.objects.filter(date=today, path=path).update(views=F("views") + 1)

        key = visitor_hash(request, today)
        updated = DailyVisitor.objects.filter(date=today, visitor=key).update(
            views=F("views") + 1, last_seen=timezone.now())
        if not updated:
            try:
                with transaction.atomic():
                    DailyVisitor.objects.create(date=today, visitor=key, views=1, first_page=path,
                                                referrer=referrer_domain(request))
                cache.delete(TOTAL_CACHE_KEY)
            except IntegrityError:
                DailyVisitor.objects.filter(date=today, visitor=key).update(views=F("views") + 1)


class VisitorCounterMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            if should_count(request, response):
                record(request)
        except Exception:  # counting must never break a page
            logger.exception("Visitor counting failed")
        return response
