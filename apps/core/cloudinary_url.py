"""Parsing of the Cloudinary connection value (pure Python: also imported by config/settings.py)."""

import re

VALID = re.compile(r"cloudinary://[^:@\s]+:[^@\s]+@[\w-]+")


def _is_placeholder(part):
    return not part or re.fullmatch(r"(your[_-]?)?(api[_-]?)?(key|secret|cloud[_-]?name)", part, re.I) is not None


def normalize_cloudinary_url(value):
    """Return cloudinary://KEY:SECRET@CLOUD from what was pasted, accepting the common variants:
    "CLOUDINARY_URL=cloudinary://…", <brackets> left around the values, a missing "cloudinary:",
    quotes or spaces, and the dashboard's template "cloudinary://<your_api_key>:<your_api_secret>@cloud"
    pasted together with "API Key: …" / "API Secret: …" lines (those lines then supply the real values)."""
    text = (value or "").replace("<", "").replace(">", "")
    if not text.strip():
        return ""
    key = secret = cloud = ""
    match = (re.search(r"(?:cloudinary:)?//\s*([^\s:@'\"]+)\s*:\s*([^\s@'\"]+)\s*@\s*([\w-]+)", text)
             or re.search(r"(?:^|=|\s)['\"]?([^\s:@'\"=]+):([^\s@'\"]+)@([\w-]+)", text))
    if match:
        key, secret, cloud = match.groups()
    labels = {
        "key": re.search(r"(?im)^\s*api[\s_-]*key\s*[:=]\s*['\"]?([\w-]+)", text),
        "secret": re.search(r"(?im)^\s*api[\s_-]*secret\s*[:=]\s*['\"]?([\w-]+)", text),
        "cloud": re.search(r"(?im)^\s*cloud[\s_-]*name\s*[:=]\s*['\"]?([\w-]+)", text),
    }
    if _is_placeholder(key) and labels["key"]:
        key = labels["key"].group(1)
    if _is_placeholder(secret) and labels["secret"]:
        secret = labels["secret"].group(1)
    if _is_placeholder(cloud) and labels["cloud"]:
        cloud = labels["cloud"].group(1)
    if key and secret and cloud and not any(map(_is_placeholder, (key, secret, cloud))):
        return f"cloudinary://{key}:{secret}@{cloud}"
    return re.sub(r"\s+", " ", text.strip())  # not usable: returned as-is so callers can report its shape


def is_valid(url):
    """Right shape AND real values (the dashboard's "your_api_key"/"your_api_secret" template is rejected)."""
    if not url or VALID.fullmatch(url) is None:
        return False
    key, _, rest = url[len("cloudinary://"):].partition(":")
    secret, _, cloud = rest.rpartition("@")
    return not any(map(_is_placeholder, (key, secret, cloud)))


def masked_shape(value):
    """The value's structure with every letter/digit hidden, e.g. cloudinary://xxxx:xxxx@xxxx (safe to log)."""
    head = "cloudinary://" if value.startswith("cloudinary://") else ""
    return head + re.sub(r"[A-Za-z0-9]", "x", value[len(head):])
