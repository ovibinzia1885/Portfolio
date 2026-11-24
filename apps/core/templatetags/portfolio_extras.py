from django import template

register = template.Library()


@register.filter
def lines(value):
    """Split multi-line text into a list of non-empty, stripped lines."""
    return [line.strip(" -*•\t") for line in str(value or "").splitlines() if line.strip()]


@register.filter
def csv(value):
    """Split comma separated text into a list of stripped items."""
    return [item.strip() for item in str(value or "").split(",") if item.strip()]


@register.simple_tag(takes_context=True)
def querystring_without(context, *names):
    """Current GET params as a query string, excluding the given names."""
    params = context["request"].GET.copy()
    for name in names:
        params.pop(name, None)
    encoded = params.urlencode()
    return f"&{encoded}" if encoded else ""
