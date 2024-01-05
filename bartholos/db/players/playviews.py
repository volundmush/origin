from bartholos.db.players.models import PlayviewDB
from bartholos.db.autoproxy.models import AutoProxyBase
from bartholos.db.players.managers import PlayviewManager


class DefaultPlayview(PlayviewDB, metaclass=AutoProxyBase):
    objects = PlayviewManager()
