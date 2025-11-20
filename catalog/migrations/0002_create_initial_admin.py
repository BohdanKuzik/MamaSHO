from django.db import migrations


def create_initial_admin(apps, schema_editor):
    import os

    from django.contrib.auth import get_user_model

    # Only run if explicitly enabled
    if os.getenv("AUTO_CREATE_SUPERUSER", "false").lower() != "true":
        return

    User = get_user_model()

    username = os.getenv("ADMIN_USERNAME", "admin")
    email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    password = os.getenv("ADMIN_PASSWORD", "admin123")

    # Idempotent: if any superuser exists, do nothing
    if User.objects.filter(is_superuser=True).exists():
        return

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)


def noop_reverse(apps, schema_editor):
    # No reverse operation
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_initial_admin, noop_reverse),
    ]
