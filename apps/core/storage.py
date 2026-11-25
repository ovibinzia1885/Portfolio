"""Media storage on Cloudinary (used in production, where the server disk is temporary).

Turned on by the CLOUDINARY_URL setting (cloudinary://API_KEY:API_SECRET@CLOUD_NAME).
Without it the site keeps using the local media/ folder, as in development.

How names map to Cloudinary:
- every file lives under the "portfolio/" folder;
- images (jpg, png, webp, gif) are "image" resources, stored without the extension
  (Cloudinary adds the format itself);
- everything else (PDF, Word) is a "raw" resource, stored with its extension, so it is
  delivered as the original file.
The name saved in the database stays the same as locally (e.g. "resume/cv.pdf"), so a
database copied from the local site points to the same files after `restore_site`.
"""

import posixpath
import urllib.request
from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}
FOLDER = "portfolio"


def parse_cloudinary_url(url):
    """cloudinary://KEY:SECRET@CLOUD -> dict for cloudinary.config()."""
    parsed = urlparse(url)
    if parsed.scheme != "cloudinary" or not (parsed.username and parsed.password and parsed.hostname):
        raise ImproperlyConfigured("CLOUDINARY_URL must look like cloudinary://API_KEY:API_SECRET@CLOUD_NAME")
    return {"cloud_name": parsed.hostname, "api_key": parsed.username, "api_secret": parsed.password, "secure": True}


@deconstructible
class CloudinaryStorage(Storage):
    def __init__(self, cloudinary_url=None):
        from django.conf import settings

        self.cloudinary_url = cloudinary_url or getattr(settings, "CLOUDINARY_URL", "")
        self._configured = False

    # --- helpers -----------------------------------------------------------
    def _sdk(self):
        import cloudinary

        if not self._configured:
            cloudinary.config(**parse_cloudinary_url(self.cloudinary_url))
            self._configured = True

    @staticmethod
    def _split(name):
        """(public_id, resource_type, format) for a storage name."""
        name = name.replace("\\", "/").lstrip("/")
        base, ext = posixpath.splitext(name)
        ext = ext.lower().lstrip(".")
        if ext in IMAGE_EXTENSIONS:
            return f"{FOLDER}/{base}", "image", ext
        return f"{FOLDER}/{name}", "raw", None

    # --- Storage API ------------------------------------------------------
    def _save(self, name, content):
        self._sdk()
        from cloudinary import uploader

        public_id, resource_type, _ = self._split(name)
        content.seek(0)
        uploader.upload(content, public_id=public_id, resource_type=resource_type,
                        overwrite=True, invalidate=True, use_filename=False, unique_filename=False)
        return name

    def _open(self, name, mode="rb"):
        return ContentFile(self._download(name), name=name)

    def _download(self, name):
        """File bytes. Documents use a signed API download: free Cloudinary accounts block public
        delivery of PDF files (HTTP 401), but the signed download always works."""
        public_id, resource_type, _ = self._split(name)
        if resource_type == "raw":
            from cloudinary.utils import private_download_url

            self._sdk()
            source = private_download_url(public_id, "", resource_type="raw", type="upload")
        else:
            source = self.cdn_url(name)
        with urllib.request.urlopen(source, timeout=30) as response:
            return response.read()

    def _resource(self, name):
        self._sdk()
        from cloudinary import api
        from cloudinary.exceptions import NotFound

        public_id, resource_type, _ = self._split(name)
        try:
            return api.resource(public_id, resource_type=resource_type)
        except NotFound:
            return None

    def exists(self, name):
        return self._resource(name) is not None

    def size(self, name):
        resource = self._resource(name)
        if resource is None:
            raise FileNotFoundError(name)
        return resource.get("bytes", 0)

    def delete(self, name):
        self._sdk()
        from cloudinary import uploader

        public_id, resource_type, _ = self._split(name)
        uploader.destroy(public_id, resource_type=resource_type, invalidate=True)

    def url(self, name):
        """Images: straight from Cloudinary's CDN. Documents (PDF, Word): through this site
        (/files/<name>), which fetches them with a signed download (see _download)."""
        if self._split(name)[1] == "raw":
            from django.urls import reverse

            return reverse("media_file", args=[name.replace("\\", "/").lstrip("/")])
        return self.cdn_url(name)

    def cdn_url(self, name):
        from cloudinary.utils import cloudinary_url

        self._sdk()
        public_id, resource_type, fmt = self._split(name)
        options = {"resource_type": resource_type, "secure": True}
        if fmt:
            options["format"] = fmt
        return cloudinary_url(public_id, **options)[0]


@deconstructible
class ConfiguredMediaStorage(Storage):
    """Production storage when the server has no usable CLOUDINARY_URL: uses the Cloudinary connection
    saved in Admin > Site settings, or the local media folder while none is saved.
    The choice is re-checked at most once a minute (and immediately after the setting is saved)."""

    _target = None
    _checked_at = 0.0
    CHECK_EVERY = 60

    @classmethod
    def reset(cls):
        cls._target = None

    @classmethod
    def target(cls):
        import time

        if cls._target is None or time.monotonic() - cls._checked_at > cls.CHECK_EVERY:
            cls._target = cls._resolve()
            cls._checked_at = time.monotonic()
        return cls._target

    @staticmethod
    def _resolve():
        from django.core.files.storage import FileSystemStorage
        from django.db import DatabaseError

        from .cloudinary_url import is_valid
        from .models import SiteSetting

        try:
            setting = SiteSetting.objects.first()
        except DatabaseError:  # e.g. during the first migrate
            setting = None
        if setting and is_valid(setting.cloudinary_url):
            return CloudinaryStorage(setting.cloudinary_url)
        return FileSystemStorage()

    @property
    def is_cloudinary(self):
        return isinstance(self.target(), CloudinaryStorage)

    # every Storage operation goes to the chosen storage
    def _save(self, name, content):
        return self.target()._save(name, content)

    def _open(self, name, mode="rb"):
        return self.target()._open(name, mode)

    def exists(self, name):
        return self.target().exists(name)

    def size(self, name):
        return self.target().size(name)

    def delete(self, name):
        return self.target().delete(name)

    def url(self, name):
        return self.target().url(name)

    def get_available_name(self, name, max_length=None):
        return self.target().get_available_name(name, max_length=max_length)
