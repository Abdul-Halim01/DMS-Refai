from django.apps import AppConfig


class EdaAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stats'

    def ready(self):
        from . import cleanup
        cleanup.cleanup_thread.start()
