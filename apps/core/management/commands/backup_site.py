"""Back up the whole site (database + uploaded files) into one .zip file.

    python manage.py backup_site                      -> backups/site-backup-<date>.zip
    python manage.py backup_site --output my.zip

Works the same locally and against production (Neon + Cloudinary): the files are read through the
active storage. Restore with `python manage.py restore_site <zip>`.
"""

import io
import json
import zipfile
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.management import BaseCommand, call_command
from django.db import models
from django.utils import timezone

# Rebuilt by `migrate` (or not worth keeping)
EXCLUDE = ["contenttypes", "auth.permission", "sessions", "admin.logentry"]


def media_names():
    """Every file name stored in any FileField/ImageField of the project."""
    names = set()
    for model in apps.get_models():
        for field in model._meta.get_fields():
            if isinstance(field, models.FileField):
                names.update(n for n in model._default_manager.values_list(field.name, flat=True) if n)
    return sorted(names)


class Command(BaseCommand):
    help = "Save the database and all uploaded files into one zip (see restore_site)."

    def add_arguments(self, parser):
        parser.add_argument("--output", help="Zip file to write (default: backups/site-backup-<date>.zip)")

    def handle(self, *args, **options):
        output = Path(options["output"] or settings.BASE_DIR / "backups" /
                      f"site-backup-{timezone.localtime():%Y%m%d-%H%M}.zip")
        output.parent.mkdir(parents=True, exist_ok=True)

        data = io.StringIO()
        call_command("dumpdata", exclude=EXCLUDE, natural_foreign=True, natural_primary=True,
                     indent=1, stdout=data)
        names = media_names()
        missing = []
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("data.json", data.getvalue())
            for name in names:
                try:
                    with default_storage.open(name, "rb") as handle:
                        archive.writestr(f"media/{name}", handle.read())
                except OSError:
                    missing.append(name)
            archive.writestr("manifest.json", json.dumps(
                {"created": timezone.now().isoformat(), "files": len(names) - len(missing), "missing": missing},
                indent=1))

        rows = len(json.loads(data.getvalue()))
        self.stdout.write(self.style.SUCCESS(
            f"Backup written: {output}  ({rows} database rows, {len(names) - len(missing)} files)"))
        for name in missing:
            self.stdout.write(self.style.WARNING(f"  file not found, skipped: {name}"))
