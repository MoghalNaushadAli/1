from datetime import datetime
from pathlib import Path
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a timestamped backup of the SQLite database."

    def add_arguments(self, parser):
        parser.add_argument("--directory", default="backups")

    def handle(self, *args, **options):
        source = Path(settings.DATABASES["default"]["NAME"])
        destination_dir = Path(options["directory"])
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / f"db-{datetime.now():%Y%m%d-%H%M%S}.sqlite3"
        shutil.copy2(source, destination)
        self.stdout.write(self.style.SUCCESS(f"Database backup created: {destination}"))