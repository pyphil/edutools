from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from appointment.models import Appointment


class Command(BaseCommand):
    help = (
        "Löscht Termine (inkl. personenbezogener Daten), die mehr als --days Tage zurückliegen. "
        "Geeignet für einen regelmäßigen Cronjob."
    )

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=30,
                            help="Termine löschen, die älter als so viele Tage sind (Standard: 30).")
        parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen, nichts löschen.")

    def handle(self, *args, days, dry_run, **options):
        cutoff = timezone.localdate() - timedelta(days=days)
        past = Appointment.objects.filter(date__lt=cutoff)
        count = past.count()
        if dry_run:
            self.stdout.write(f"{count} Termine vor dem {cutoff:%d.%m.%Y} würden gelöscht.")
            return
        past.delete()
        self.stdout.write(self.style.SUCCESS(f"{count} Termine vor dem {cutoff:%d.%m.%Y} gelöscht."))
