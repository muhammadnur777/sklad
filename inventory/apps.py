from django.apps import AppConfig


class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory'
    verbose_name = 'Sklad'

    def ready(self):
        import inventory.signals

# from django.apps import AppConfig


# class InventoryConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'inventory'
#     verbose_name = 'Sklad'