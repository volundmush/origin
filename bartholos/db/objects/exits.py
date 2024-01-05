from bartholos.db.objects.models import ExitDB
from bartholos.db.autoproxy.models import AutoProxyBase
from bartholos.db.objects.managers import ExitManager


class DefaultExit(ExitDB, metaclass=AutoProxyBase):
    objects = ExitManager()



