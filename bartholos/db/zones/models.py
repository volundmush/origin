from django.db import models

from bartholos.db.autoproxy.models import AutoProxyObject
from bartholos.db.zones.managers import ZoneDBManager
from django.contrib.contenttypes.fields import GenericRelation

from bartholos.db.properties.attributes import AttributeHandler
from mudforge.utils import lazy_property


class ZoneDB(AutoProxyObject):
    __proxy_family__ = "zones"
    __defaultclasspath__ = "bartholos.db.objects.zones.DefaultZone"
    __applabel__ = "objects"

    objects = ZoneDBManager()

    id = models.OneToOneField(
        "objects.ObjectDB",
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="zone_data",
    )

    attr_data = GenericRelation("properties.Attribute", related_name="zones")

    def __str__(self):
        return str(self.id)

    @lazy_property
    def attributes(self):
        return AttributeHandler(self)
