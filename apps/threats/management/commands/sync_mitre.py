from django.core.management.base import BaseCommand
from mitre.client import get_mitre_client
from mitre import sync


class Command(BaseCommand):
    help = "Download and upsert MITRE ATT&CK groups, campaigns, and techniques into MongoDB."

    def add_arguments(self, parser):
        parser.add_argument(
            "--actors-only",
            action="store_true",
            help="Only sync threat actor groups.",
        )
        parser.add_argument(
            "--campaigns-only",
            action="store_true",
            help="Only sync campaigns.",
        )

    def handle(self, *args, **options):
        self.stdout.write("Loading MITRE ATT&CK data...")
        client = get_mitre_client()
        self.stdout.write(self.style.SUCCESS("MITRE client loaded."))

        actors_only = options["actors_only"]
        campaigns_only = options["campaigns_only"]
        run_all = not actors_only and not campaigns_only

        if run_all or actors_only:
            self.stdout.write("Syncing threat actors...")
            sync.sync_actors(client, stdout=self.stdout)

        if run_all or campaigns_only:
            self.stdout.write("Syncing campaigns...")
            sync.sync_campaigns(client, stdout=self.stdout)

        self.stdout.write(self.style.SUCCESS("MITRE sync complete."))
