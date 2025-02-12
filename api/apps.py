from django.apps import AppConfig
import importlib

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        importlib.import_module('api.signals')
