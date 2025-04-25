from django.apps import AppConfig
from . import cleanup


class EdaAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stats'

    def ready(self):
        cleanup.cleanup_thread.start()
