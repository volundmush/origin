from bartholos.db.objects.models import ObjectDB
from bartholos.db.autoproxy.models import AutoProxyBase
from bartholos.db.objects.managers import ObjectManager


class DefaultObject(ObjectDB, metaclass=AutoProxyBase):
    objects = ObjectManager()



