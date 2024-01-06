def setup_django(core):
    import os

    os.environ["DJANGO_SETTINGS_MODULE"] = "game_code.django_settings"
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
    import django

    django.setup()
