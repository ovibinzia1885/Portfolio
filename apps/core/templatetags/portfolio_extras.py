import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def lines(value):
    """Split multi-line text into a list of non-empty, stripped lines."""
    return [line.strip(" -*•\t") for line in str(value or "").splitlines() if line.strip()]


@register.filter
def csv(value):
    """Split comma separated text into a list of stripped items."""
    return [item.strip() for item in str(value or "").split(",") if item.strip()]


@register.filter
def soft_wrap(value):
    """Escape text and allow a line break after "/" (e.g. "Integration/Continuous" on phones)."""
    return mark_safe(escape(value or "").replace("/", "/<wbr>"))  # safe: escaped first


@register.filter
def highlight_author(authors, profile):
    """Escape an author list and wrap the site owner's name (from `profile`) in <strong>."""
    text = escape(authors or "")
    name = escape(getattr(profile, "full_name", "") or "").strip()
    if name:
        # whole words only: a short name must not be bolded inside a longer one ("Ali" in "Alice")
        text = re.sub(rf"(?<!\w){re.escape(name)}(?!\w)", lambda m: f"<strong>{m.group(0)}</strong>", text, flags=re.IGNORECASE)
    return mark_safe(text)  # safe: input escaped above, only <strong> added


@register.simple_tag(takes_context=True)
def dashboard(context):
    """Admin dashboard data (cards, quick-add links, profile). Used by templates/admin/index.html."""
    from apps.core.dashboard import dashboard as build_dashboard

    return build_dashboard(context)


@register.simple_tag(takes_context=True)
def querystring_without(context, *names):
    """Current GET params as a query string, excluding the given names."""
    params = context["request"].GET.copy()
    for name in names:
        params.pop(name, None)
    encoded = params.urlencode()
    return f"&{encoded}" if encoded else ""
