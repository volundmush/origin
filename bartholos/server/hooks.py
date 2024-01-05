
def setup_django(core):
    import os
    os.environ['DJANGO_SETTINGS_MODULE'] = 'game_code.django_settings'
    import django
    django.setup()
