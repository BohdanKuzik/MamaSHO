from __future__ import annotations

from django.core.management.base import BaseCommand

from catalog.models import ProductReservation


class Command(BaseCommand):
    help = "Clean up expired product reservations (older than 15 minutes)"

    def handle(self: "Command", *args: str, **options: object) -> None:
        count = ProductReservation.cleanup_expired()
        if count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully cleaned up {count} expired reservation(s)."
                )
            )
        else:
            self.stdout.write("No expired reservations to clean up.")
