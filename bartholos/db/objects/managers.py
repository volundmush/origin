from bartholos.db.autoproxy.managers import AutoProxyManager, AutoProxyObjectManager


class ObjectDBManager(AutoProxyObjectManager):
    pass



class ObjectManager(ObjectDBManager, AutoProxyManager):
    pass


class RoomDBManager(AutoProxyObjectManager):
    pass



class RoomManager(RoomDBManager, AutoProxyManager):
    pass


class ExitDBManager(AutoProxyObjectManager):
    pass



class ExitManager(ExitDBManager, AutoProxyManager):
    pass