from bartholos.db.objects.models import RoomDB
from bartholos.db.autoproxy.models import AutoProxyBase
from bartholos.db.objects.managers import RoomManager


class DefaultRoom(RoomDB, metaclass=AutoProxyBase):
    objects = RoomManager()
