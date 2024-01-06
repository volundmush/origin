from bartholos.db.autoproxy.managers import AutoProxyManager, AutoProxyObjectManager
from django.contrib.auth.models import UserManager as BaseUserManager


class UserDBManager(AutoProxyObjectManager, BaseUserManager):
    pass


class UserManager(UserDBManager, AutoProxyManager):
    pass
