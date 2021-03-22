from django.apps import AppConfig


class JudgeConfig(AppConfig):
    name = 'judge'

    def ready(self):
        import judge.signals

