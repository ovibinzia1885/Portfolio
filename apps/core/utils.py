"""Shared helpers used across apps."""

import uuid
from datetime import date

from django.utils.text import slugify


def unique_slugify(instance, value, slug_field="slug"):
    """Return a slug for `value` that is unique for the instance's model.

    Falls back to a random token for titles without ASCII/unicode letters.
    """
    base = slugify(value, allow_unicode=True)
    if len(base) > 60:  # cut at a word boundary, never mid-word or with a trailing hyphen
        cut = base[:61]
        base = cut[:cut.rfind("-")] if "-" in cut else base[:60]
    base = base.strip("-") or uuid.uuid4().hex[:8]
    model = instance.__class__
    slug, counter = base, 2
    while model.objects.filter(**{slug_field: slug}).exclude(pk=instance.pk).exists():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


def format_duration(start, end=None):
    """Human readable duration like '3 yrs 10 mos' (months counted inclusively)."""
    if not start:
        return ""
    end = end or date.today()
    months = max((end.year - start.year) * 12 + end.month - start.month + 1, 1)
    years, rest = divmod(months, 12)
    parts = []
    if years:
        parts.append(f"{years} yr{'s' if years > 1 else ''}")
    if rest:
        parts.append(f"{rest} mo{'s' if rest > 1 else ''}")
    return " ".join(parts)


def format_date_range(start, end=None, present=False):
    """e.g. 'Sep 2018 - Jun 2022' or 'Jan 2023 - Present'."""
    if not start:
        return ""
    left = start.strftime("%b %Y")
    if end:
        right = end.strftime("%b %Y")
    else:
        right = "Present" if present else ""
    return f"{left} - {right}" if right else left
