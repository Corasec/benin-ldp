from django.core.management.base import BaseCommand
from usermanager.models import User


class Command(BaseCommand):
    help = 'Create 100 user accounts with specific emails and usernames'

    def handle(self, *args, **kwargs):
        users_created = 0
        for i in range(1, 101):
            email = f"training{i}@example.com"
            username = f"training{i}"

            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    email=email,
                    username=username,
                    password="training123",
                )
                user.is_approved = True  # Set flags if necessary
                user.save()
                users_created += 1
                self.stdout.write(self.style.SUCCESS(f"Created user: {email}"))
            else:
                self.stdout.write(self.style.WARNING(f"User with email {email} already exists"))

        self.stdout.write(self.style.SUCCESS(f"Successfully created {users_created} users"))