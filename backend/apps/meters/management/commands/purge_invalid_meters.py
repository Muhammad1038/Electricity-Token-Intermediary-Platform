"""
Management command: purge_invalid_meters

Re-validates every active meter profile against the live VTPass API.
Any meter that fails validation (wrong meter number, wrong DISCO, sandbox
test number, or no registered customer name) is permanently deleted from
the database and its Redis cache entry is cleared.

Usage:
    python manage.py purge_invalid_meters
    python manage.py purge_invalid_meters --dry-run      # preview only, no deletes
    python manage.py purge_invalid_meters --disco AEDC   # only one DISCO
"""
import time

from django.core.cache import cache
from django.core.management.base import BaseCommand

from apps.meters.models import MeterProfile
from apps.meters.services import _cache_key, validate_meter_with_disco


class Command(BaseCommand):
    help = "Re-validate all saved meters against live VTPass and purge any that are invalid."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show which meters would be deleted without actually deleting them.",
        )
        parser.add_argument(
            "--disco",
            type=str,
            default=None,
            help="Restrict purge to a specific DISCO code (e.g. AEDC, KEDCO).",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        filter_disco = options.get("disco")

        qs = MeterProfile.objects.filter(is_active=True)
        if filter_disco:
            qs = qs.filter(disco=filter_disco.upper())

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.WARNING("No active meter profiles found."))
            return

        mode = "[DRY RUN] " if dry_run else ""
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"{mode}Validating {total} meter profile(s) against live VTPass..."
            )
        )

        purged = 0
        kept = 0
        errors = 0

        for meter in qs.iterator():
            label = f"{meter.disco} / {meter.meter_number} (user={meter.user_id}, id={meter.id})"

            # Always clear cached result first — force a fresh live call
            cache.delete(_cache_key(meter.meter_number, meter.disco))

            try:
                result = validate_meter_with_disco(
                    meter_number=meter.meter_number,
                    disco=meter.disco,
                    meter_type=meter.meter_type.lower(),
                )
            except Exception as exc:  # noqa: BLE001
                self.stdout.write(
                    self.style.ERROR(f"  ERROR  {label} — could not reach VTPass: {exc}")
                )
                errors += 1
                continue

            # Small delay between calls so we don't hammer VTPass
            time.sleep(0.5)

            if result.get("is_valid"):
                # Update stored owner name / address / type with fresh live data
                if not dry_run:
                    updated_fields = []
                    new_name = result.get("meter_owner_name", "")
                    new_addr = result.get("meter_address", "")
                    new_type = result.get("meter_type", meter.meter_type)

                    if new_name and meter.meter_owner_name != new_name:
                        meter.meter_owner_name = new_name
                        updated_fields.append("meter_owner_name")
                    if new_addr and meter.meter_address != new_addr:
                        meter.meter_address = new_addr
                        updated_fields.append("meter_address")
                    if new_type and meter.meter_type != new_type.upper():
                        meter.meter_type = new_type.upper()
                        updated_fields.append("meter_type")

                    # Auto-update nickname if it's still the old owner name placeholder
                    if (
                        new_name
                        and meter.nickname == meter.meter_owner_name
                        and meter.meter_owner_name != new_name
                    ):
                        meter.nickname = new_name
                        updated_fields.append("nickname")

                    if updated_fields:
                        updated_fields.append("updated_at")
                        meter.save(update_fields=updated_fields)
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  KEPT   {label} — valid ({result.get('meter_owner_name')}) [updated: {', '.join(updated_fields)}]"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  KEPT   {label} — valid ({result.get('meter_owner_name')})"
                            )
                        )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  KEPT   {label} — valid ({result.get('meter_owner_name')})"
                        )
                    )
                kept += 1
            else:
                reason = result.get("error") or "Invalid meter / not registered with this DISCO"
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(f"  WOULD DELETE  {label} — {reason}")
                    )
                else:
                    # Try hard delete first; fall back to soft-delete if protected by transactions
                    cache.delete(_cache_key(meter.meter_number, meter.disco))
                    try:
                        meter.delete()
                        self.stdout.write(
                            self.style.WARNING(f"  DELETED  {label} — {reason}")
                        )
                    except Exception:  # ProtectedError — has linked transactions
                        meter.is_active = False
                        meter.save(update_fields=["is_active", "updated_at"])
                        self.stdout.write(
                            self.style.WARNING(
                                f"  DEACTIVATED  {label} — {reason} "
                                f"(kept record because it has transaction history)"
                            )
                        )
                purged += 1

        self.stdout.write("")
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"{mode}Done.  Kept: {kept}  |  {'Would delete' if dry_run else 'Deleted'}: {purged}  |  Errors: {errors}"
            )
        )

        if errors:
            self.stdout.write(
                self.style.WARNING(
                    "Some meters could not be checked due to VTPass errors. "
                    "Run the command again to retry them."
                )
            )
