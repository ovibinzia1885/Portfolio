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
        parser.add_argument("--replace", action="store_true",
                            help="Empty the target database first (all rows deleted), then load the backup. "
                                 "Use for a fresh copy, e.g. after an interrupted first restore.")

    def handle(self, *args, **options):
        path = Path(options["zip_file"])
        if not path.is_file():
            raise CommandError(f"Backup not found: {path}")
        if Profile.objects.exists() and not (options["force"] or options["replace"]):
            raise CommandError("This database already has a profile. Use --force to load the backup anyway.")
        self.check_media_storage()
        if options["replace"]:
            call_command("flush", interactive=False, verbosity=0)  # empty tables; content types are recreated
            self.stdout.write("Target database emptied.")

        with zipfile.ZipFile(path) as archive, tempfile.TemporaryDirectory() as tmp:
            data_file = Path(tmp) / "data.json"
            data_file.write_bytes(archive.read("data.json"))
            try:
                with transaction.atomic():
                    call_command("loaddata", str(data_file), verbosity=0)
            except Exception as exc:  # show the reason in one line instead of a long traceback
                raise CommandError(f"Loading the database rows failed: {type(exc).__name__}: {exc}") from exc
            self.stdout.write("Database rows loaded.")

            uploaded = skipped = 0
            failed = []
            for member in archive.namelist():
                if not member.startswith("media/") or member.endswith("/"):
                    continue
                name = member[len("media/"):]
                try:
                    if default_storage.exists(name):
                        skipped += 1
                        continue
                    saved = default_storage.save(name, ContentFile(archive.read(member)))
                except Exception as exc:  # keep going; list every file that failed at the end
                    failed.append(name)
                    self.stdout.write(self.style.ERROR(f"  FAILED {name}: {type(exc).__name__}: {exc}"))
                    continue
                if saved != name:  # the database expects the original name
                    self.stdout.write(self.style.WARNING(f"  saved as {saved} instead of {name}"))
                uploaded += 1
                self.stdout.write(f"  uploaded {name}")

        if failed:
            raise CommandError(f"{len(failed)} file(s) could not be uploaded (see above). Run the command again "
                               "with --force once the problem is fixed; finished files are skipped.")
        self.stdout.write(self.style.SUCCESS(f"Restore finished: {uploaded} files uploaded, {skipped} already there."))

    def check_media_storage(self):
        """With Cloudinary: test the login first, so a wrong CLOUDINARY_URL fails before anything is loaded."""
        from django.core.files.storage import storages

        from apps.core.storage import CloudinaryStorage, ConfiguredMediaStorage

        storage = storages["default"]
        if isinstance(storage, ConfiguredMediaStorage):
            storage = storage.target()
        if not isinstance(storage, CloudinaryStorage):
            return
        try:
            storage._sdk()
            from cloudinary import api

            api.ping()
        except Exception as exc:
            raise CommandError(f"Cloudinary login failed ({type(exc).__name__}: {exc}). "
                               "Check CLOUDINARY_URL (cloudinary://API_KEY:API_SECRET@CLOUD_NAME).") from exc
        self.stdout.write("Cloudinary login OK.")
