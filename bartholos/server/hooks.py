def setup_django(core):
    import os

    os.environ["DJANGO_SETTINGS_MODULE"] = "game_code.django_settings"
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
    import django

    django.setup()


def import_validatorfuncs(core):
    import bartholos
    from mudforge.utils import callables_from_module

    for module in core.settings.VALIDATOR_FUNC_MODULES:
        for k, v in callables_from_module(module).items():
            bartholos.VALIDATORS[k] = v


def import_optionclasses(core):
    import bartholos
    from mudforge.utils import callables_from_module

    for module in core.settings.OPTION_CLASS_MODULES:
        for k, v in callables_from_module(module).items():
            bartholos.OPTION_CLASSES[k] = v
