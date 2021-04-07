from django.apps import AppConfig


class JudgeConfig(AppConfig):  # pragma: no cover
    # Avoids coverage checking for the JudgeConfig class

    name = 'judge'

    # Default type for auto fields (primary keys not assigned, as in Problem, Submission, etc.)
    # BigAutoField is the default auto field from Django 3.2
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        import judge.signals
