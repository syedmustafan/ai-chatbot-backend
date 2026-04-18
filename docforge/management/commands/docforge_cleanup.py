from django.core.management.base import BaseCommand

from docforge.services.cleanup import sweep


class Command(BaseCommand):
    help = 'Delete expired DocForge sessions (ephemeral / auto-expire)'

    def handle(self, *args, **options):
        deleted = sweep()
        self.stdout.write(self.style.SUCCESS(f'docforge_cleanup: deleted {deleted} sessions'))
