"""Save the Cloudinary connection in the database (Admin > Site settings) after testing the login.

    python manage.py set_cloudinary "cloudinary://API_KEY:API_SECRET@CLOUD_NAME"

Same as pasting it in the admin; useful when the admin is not reachable yet.
"""

from django.core.management import BaseCommand, CommandError

from apps.core.cloudinary_url import is_valid, masked_shape, normalize_cloudinary_url
from apps.core.models import SiteSetting
from apps.core.storage import CloudinaryStorage


class Command(BaseCommand):
    help = "Test and save the Cloudinary connection used for uploaded files on the live site."

    def add_arguments(self, parser):
        parser.add_argument("value")

    def handle(self, *args, **options):
        url = normalize_cloudinary_url(options["value"])
        if not is_valid(url):
            raise CommandError(f"Not a Cloudinary connection (shape: {masked_shape(url)}).")
        storage = CloudinaryStorage(url)
        try:
            storage._sdk()
            from cloudinary import api

            api.ping()
        except Exception as exc:
            raise CommandError(f"Cloudinary login failed: {type(exc).__name__}: {exc}") from exc
        setting = SiteSetting.objects.first() or SiteSetting()
        setting.cloudinary_url = url
        setting.save()
        self.stdout.write(self.style.SUCCESS(f"Cloudinary connection saved (cloud: {url.rsplit('@', 1)[-1]})."))
