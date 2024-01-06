from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericRelation

import mudforge
from bartholos.db.autoproxy.models import AutoProxyObject
from bartholos.db.users.managers import UserDBManager

from bartholos.db.properties.attributes import AttributeHandler
from mudforge.utils import lazy_property


class UserDB(AutoProxyObject, AbstractUser):
    __proxy_family__ = "users"
    __defaultclasspath__ = "bartholos.db.users.users.DefaultUser"
    __applabel__ = "users"

    objects = UserDBManager()

    class LevelChoices(models.IntegerChoices):
        DEVELOPER = 5
        ADMINISTRATOR = 4
        BUILDER = 3
        GAMEMASTER = 2
        HELPER = 1
        USER = 0

    level = models.PositiveSmallIntegerField(
        choices=LevelChoices.choices, default=LevelChoices.USER
    )

    attr_data = GenericRelation("properties.Attribute", related_name="users")

    @lazy_property
    def attributes(self):
        return AttributeHandler(self)


class Host(models.Model):
    ip = models.GenericIPAddressField(unique=True)
    hostname = models.CharField(max_length=255, null=True)


class LoginRecord(models.Model):
    host = models.ForeignKey(Host, on_delete=models.PROTECT, related_name="records")
    user = models.ForeignKey(
        UserDB, on_delete=models.CASCADE, related_name="login_records"
    )
    is_success = models.BooleanField(default=False)
    reason = models.CharField(max_length=50, null=True, blank=False)
    date_created = models.DateTimeField(auto_now_add=True, editable=True)
