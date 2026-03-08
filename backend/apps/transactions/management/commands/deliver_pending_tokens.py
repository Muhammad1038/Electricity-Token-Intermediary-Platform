"""
Management command: dispatch token delivery for ALL successful-payment transactions
across every user account that haven't received a token yet.

Usage:
    python manage.py deliver_pending_tokens          # dry-run preview
    python manage.py deliver_pending_tokens --apply  # actually dispatch tasks
"""
from django.core.management.base import BaseCommand

from apps.transactions.models import PaymentStatus, TokenStatus, Transaction


class Command(BaseCommand):
    help = "Dispatch DISCO token delivery for all paid-but-undelivered transactions (all users)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Actually dispatch Celery tasks (omit for dry-run).",
        )

    def handle(self, *args, **options):
        apply = options["apply"]

        # All users — any transaction with successful payment but token not yet delivered
        qs = Transaction.objects.filter(
            payment_status=PaymentStatus.SUCCESS,
            token_status__in=[TokenStatus.PENDING, TokenStatus.FAILED],
        ).select_related("user").order_by("created_at")

        count = qs.count()
        self.stdout.write(f"Found {count} transaction(s) needing token delivery across all accounts.")

        if count == 0:
            self.stdout.write(self.style.SUCCESS("All users are up to date. Nothing to do."))
            return

        if not apply:
            self.stdout.write(self.style.WARNING(
                "DRY RUN — pass --apply to actually dispatch tasks.\n"
            ))
            for txn in qs:
                self.stdout.write(
                    f"  • {txn.reference} | user={txn.user} "
                    f"| meter={txn.meter_number} | disco={txn.disco} "
                    f"| amount=\u20a6{txn.amount} | token_status={txn.token_status}"
                )
            return

        from apps.transactions.tasks import request_disco_token_task

        dispatched = 0
        for txn in qs:
            try:
                request_disco_token_task.delay(str(txn.id))
                dispatched += 1
                self.stdout.write(
                    f"  \u2713 Queued: {txn.reference} | user={txn.user} | meter={txn.meter_number}"
                )
            except Exception as exc:
                self.stdout.write(
                    self.style.ERROR(f"  \u2717 Failed to queue {txn.reference}: {exc}")
                )

        self.stdout.write(self.style.SUCCESS(
            f"\nDispatched {dispatched}/{count} token delivery task(s).\n"
            "Tokens will be delivered as Celery processes the queue.\n"
            "Run this command again to verify remaining count drops to 0."
        ))
