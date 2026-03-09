"""
Load customers from a CSV file into MongoDB.

Usage:
    python manage.py load_customers /path/to/company_naics_breach_research.csv

Behaviour:
  - Upserts on customer name (update existing, insert new).
  - short_name is auto-slugified from name.
  - Grants the importing analyst (--grant-user) access to all imported customers.
  - Sets has_known_breach from the data_breach column (Y/N).
  - Adds website_url, naics_code, naics_title (→ sector) from CSV columns.
  - contract_exp_date stored when present; left null when blank.
"""
import csv
import logging
from datetime import datetime, timezone

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from apps.accounts.models import User
from apps.customers.models import Customer, IndustryInfo

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import / update customers from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", help="Path to the customer CSV file")
        parser.add_argument(
            "--grant-user",
            dest="grant_user",
            default="",
            help="Username to grant access to all imported customers",
        )

    def handle(self, *args, **options):
        csv_path = options["csv_path"]
        grant_username = options["grant_user"]

        try:
            rows = self._read_csv(csv_path)
        except FileNotFoundError:
            raise CommandError(f"File not found: {csv_path}")

        now = datetime.now(tz=timezone.utc)
        imported_ids = []

        for row in rows:
            customer = self._upsert_customer(row, now)
            imported_ids.append(customer.id)

        self.stdout.write(self.style.SUCCESS(
            f"Imported/updated {len(imported_ids)} customers."
        ))

        if grant_username:
            self._grant_access(grant_username, imported_ids)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _read_csv(self, path: str) -> list[dict]:
        with open(path, newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))

    def _upsert_customer(self, row: dict, now: datetime) -> Customer:
        name = row["customer"].strip()
        short_name = slugify(name)[:50]

        naics_code_raw = row.get("naics_code", "").strip()
        naics_code = int(naics_code_raw) if naics_code_raw.isdigit() else None
        naics_title = row.get("naics_title", "").strip()

        industry = IndustryInfo(
            sector=naics_title,
            naics_code=naics_code,
        )

        website_url = row.get("customer_url", "").strip() or None

        has_known_breach = row.get("data_breach", "N").strip().upper() == "Y"

        breach_ref = row.get("data_breach_ref", "").strip()
        breach_source_refs = [breach_ref] if breach_ref else []

        contract_exp_raw = row.get("contract_exp_date", "").strip()
        contract_exp_date = None
        if contract_exp_raw:
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
                try:
                    contract_exp_date = datetime.strptime(contract_exp_raw, fmt).replace(
                        tzinfo=timezone.utc
                    )
                    break
                except ValueError:
                    continue

        existing = Customer.objects(name=name).first()

        if existing:
            existing.short_name = short_name
            existing.industry = industry
            existing.website_url = website_url
            existing.has_known_breach = has_known_breach
            existing.breach_source_refs = breach_source_refs
            existing.contract_exp_date = contract_exp_date
            existing.updated_at = now
            existing.save()
            self.stdout.write(f"  Updated: {name}")
            return existing
        else:
            customer = Customer(
                name=name,
                short_name=short_name,
                industry=industry,
                website_url=website_url,
                has_known_breach=has_known_breach,
                breach_source_refs=breach_source_refs,
                contract_exp_date=contract_exp_date,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            customer.save()
            self.stdout.write(f"  Inserted: {name}")
            return customer

    def _grant_access(self, username: str, customer_ids: list):
        user = User.objects(username=username).first()
        if not user:
            self.stderr.write(self.style.WARNING(
                f"User '{username}' not found — skipping access grant."
            ))
            return

        existing_ids = {str(i) for i in user.allowed_customer_ids}
        new_ids = [cid for cid in customer_ids if str(cid) not in existing_ids]
        user.allowed_customer_ids = list(user.allowed_customer_ids) + new_ids
        user.save()
        self.stdout.write(self.style.SUCCESS(
            f"Granted {username} access to {len(new_ids)} new customer(s) "
            f"({len(user.allowed_customer_ids)} total)."
        ))
