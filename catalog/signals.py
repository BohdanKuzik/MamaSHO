from __future__ import annotations

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Customer


@receiver(post_save, sender=User)
def create_customer(
    sender: type[User], instance: User, created: bool, **kwargs: object
) -> None:
    if created and not instance.is_staff:
        Customer.objects.create(user=instance)
