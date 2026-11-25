"""Load a backup made by `backup_site` into the CURRENT database and media storage.

Typical use: move the local site to production. In a terminal where DATABASE_URL (Neon) and
CLOUDINARY_URL are set for production:

    python manage.py migrate
    python manage.py restore_site backups/site-backup-<date>.zip

Refuses to run when the target already has a profile (so a live site is never overwritten by
accident); pass --force to load anyway.
"""

import tempfile
import zipfile
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management import BaseCommand, CommandError, call_command
from django.db import transaction

from apps.core.models import Profile


class Command(BaseCommand):
    help = "Restore the database rows and uploaded files from a backup_site zip."

    def add_arguments(self, parser):
        parser.add_argument("zip_file")
        parser.add_argument("--force", action="store_true", help="Load even if the site already has a profile.")

    def handle(self, *args, **options):
        path = Path(options["zip_file"])
        if not path.is_file():
            raise CommandError(f"Backup not found: {path}")
        if Profile.objects.exists() and not options["force"]:
            raise CommandError("This database already has a profile. Use --force to load the backup anyway.")

        with zipfile.ZipFile(path) as archive, tempfile.TemporaryDirectory() as tmp:
            data_file = Path(tmp) / "data.json"
            data_file.write_bytes(archive.read("data.json"))
            with transaction.atomic():
                call_command("loaddata", str(data_file), verbosity=0)
            self.stdout.write("Database rows loaded.")

            uploaded = skipped = 0
            for member in archive.namelist():
                if not member.startswith("media/") or member.endswith("/"):
                    continue
                name = member[len("media/"):]
                if default_storage.exists(name):
                    skipped += 1
                    continue
                saved = default_storage.save(name, ContentFile(archive.read(member)))
                if saved != name:  # the database expects the original name
                    self.stdout.write(self.style.WARNING(f"  saved as {saved} instead of {name}"))
                uploaded += 1
                self.stdout.write(f"  uploaded {name}")

        self.stdout.write(self.style.SUCCESS(f"Restore finished: {uploaded} files uploaded, {skipped} already there."))
