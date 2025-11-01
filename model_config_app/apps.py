from django.apps import AppConfig


class ModelConfigAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'model_config_app'
