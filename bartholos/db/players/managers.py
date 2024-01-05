from bartholos.db.autoproxy.managers import AutoProxyManager, AutoProxyObjectManager


class PlayviewDBManager(AutoProxyObjectManager):
    pass


class PlayviewManager(PlayviewDBManager, AutoProxyManager):
    pass
