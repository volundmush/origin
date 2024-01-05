from bartholos.db.autoproxy.managers import AutoProxyManager, AutoProxyObjectManager


class UserDBManager(AutoProxyObjectManager):
    pass


class UserManager(UserDBManager, AutoProxyManager):
    pass
