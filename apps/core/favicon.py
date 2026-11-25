"""Browser icon (favicon / app icons) generated from the profile photo.

The photo is cropped to a square (slightly towards the top, where the face is), resized and cached.
Changing the photo in the admin changes the icon automatically (the URL carries a version).
"""

from io import BytesIO

from django.core.cache import cache
from django.http import Http404, HttpResponse
from django.views.decorators.http import require_GET
from PIL import Image, ImageDraw, ImageOps

from .models import Profile

SIZES = {32, 180, 192, 512}
ROUNDED = {32, 192, 512}  # 180 = Apple touch icon: iOS rounds it itself and dislikes transparency


def make_icon(photo_file, size):
    with Image.open(photo_file) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        w, h = im.size
        side = min(w, h)
        left = (w - side) // 2
        top = int((h - side) * 0.25)  # keep the face, not the shirt
        im = im.crop((left, top, left + side, top + side)).resize((size, size), Image.LANCZOS)
    if size in ROUNDED:
        mask = Image.new("L", (size * 4, size * 4), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, size * 4, size * 4), radius=size, fill=255)
        im.putalpha(mask.resize((size, size), Image.LANCZOS))
    buf = BytesIO()
    im.save(buf, "PNG", optimize=True)
    return buf.getvalue()


@require_GET
def favicon(request, size=32):
    if size not in SIZES:
        raise Http404
    profile = Profile.objects.first()
    if not profile or not profile.photo:
        raise Http404("No profile photo.")
    key = f"favicon:{profile.photo.name}:{int(profile.updated_at.timestamp())}:{size}"
    data = cache.get(key)
    if data is None:
        try:
            data = make_icon(profile.photo, size)
        except (OSError, ValueError):  # photo missing on disk or not a readable image
            raise Http404("Profile photo not readable.")
        cache.set(key, data, 60 * 60 * 24)
    response = HttpResponse(data, content_type="image/png")
    response["Cache-Control"] = "public, max-age=86400"
    return response
