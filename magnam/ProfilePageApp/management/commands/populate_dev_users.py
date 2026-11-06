from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from utils.helper_functions import send_verification_email

NUM_OF_TEST_USERS = 10


class Command(BaseCommand):
    help = "Create default test users for development"

    @transaction.atomic
    def handle(self, *args, **options):
        for i in range(NUM_OF_TEST_USERS):
            username = f"user{i}"
            email = f"user{i}@gmail.com"
            password = f"user{i}pass"

            if username == "user0":
                user = User.objects.create_superuser(
                    username=username, email=email, password=password
                )
                send_verification_email(user_email=email, token=user.profile.verification_token)
            else:
                user = User.objects.create_user(
                    username=username, email=email, password=password
                )
                send_verification_email(user_email=email, token=user.profile.verification_token)
            self.stdout.write(self.style.SUCCESS(f"Created user {username}"))
