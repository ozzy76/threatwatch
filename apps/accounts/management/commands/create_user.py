import getpass
import datetime
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from apps.accounts.models import User, ROLE_ANALYST, ROLE_ADMIN


class Command(BaseCommand):
    help = "Pre-provision an analyst account (no public registration)."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--email", required=True)
        parser.add_argument("--first-name", default="")
        parser.add_argument("--last-name", default="")
        parser.add_argument("--staff", action="store_true", default=False)
        parser.add_argument(
            "--role",
            choices=[ROLE_ANALYST, ROLE_ADMIN],
            default=ROLE_ANALYST,
            help="Role for the new user (default: analyst)",
        )

    def handle(self, *args, **options):
        username = options["username"]
        email = options["email"]

        if User.objects(username=username).first():
            raise CommandError(f"User '{username}' already exists.")

        password = getpass.getpass(f"Password for {username}: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            raise CommandError("Passwords do not match.")

        try:
            validate_password(password)
        except ValidationError as exc:
            raise CommandError("; ".join(exc.messages))

        user = User(
            username=username,
            email=email,
            first_name=options["first_name"],
            last_name=options["last_name"],
            is_active=True,
            is_staff=options["staff"],
            role=options["role"],
            date_joined=datetime.datetime.now(datetime.timezone.utc),
        )
        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS(f"User '{username}' created successfully."))
