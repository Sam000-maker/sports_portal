from django.apps import AppConfig

class PlayersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "players"

    def ready(self):
        # Connect signals at runtime so get_user_model() resolves correctly
        from django.contrib.auth import get_user_model
        from django.db.models.signals import post_save
        from . import signals

        User = get_user_model()
        post_save.connect(
            signals.create_profile_for_student,
            sender=User,
            dispatch_uid="players_create_profile_for_student",
        )
