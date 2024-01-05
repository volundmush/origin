from mudforge.launcher import Launcher

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'game_code.django_settings'


class BartholosLauncher(Launcher):

    def operation_passthru(self, op, args, unknown):
        """
        God only knows what people typed here. Let their program figure it out! Overload this to
        process the operation.
        """
        import django
        django.setup()
        from django.core import management
        management.call_command(*([op] + unknown))
