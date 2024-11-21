from django.core.management.base import BaseCommand
from usermanager.models import User

class Command(BaseCommand):
    help = 'Remove all fake user accounts'

    def handle(self, *args, **kwargs):
        deleted_count, _ = User.objects.filter(email__startswith="training").delete()
        self.stdout.write(self.style.SUCCESS(f"Successfully deleted {deleted_count} fake users"))