from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "catalog"

    def ready(self: "CatalogConfig") -> None:
        import catalog.signals  # noqa: F401
