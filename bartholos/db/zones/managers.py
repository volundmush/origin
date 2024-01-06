from bartholos.db.autoproxy.managers import AutoProxyManager, AutoProxyObjectManager


class ZoneDBManager(AutoProxyObjectManager):
    pass


class ZoneManager(ZoneDBManager, AutoProxyManager):
    pass
