from django.db import models
from django.contrib.contenttypes.fields import GenericRelation

from bartholos.db.idmapper.models import SharedMemoryModel
from bartholos.db.autoproxy.models import AutoProxyObject
from bartholos.db.objects.managers import ObjectDBManager

from bartholos.db.properties.attributes import AttributeHandler
from mudforge.utils import lazy_property


class ObjectDB(AutoProxyObject):
    __proxy_family__ = "objects"
    __defaultclasspath__ = "bartholos.db.objects.objects.DefaultObject"
    __applabel__ = "objects"

    objects = ObjectDBManager()

    generation = models.BigIntegerField(null=False, blank=False)

    name = models.CharField(blank=False, null=True, max_length=255)

    lock_data = models.JSONField(blank=False, null=True, default=dict)

    in_zone = models.ForeignKey(
        "objects.ZoneDB",
        null=True,
        blank=False,
        related_name="contents",
        on_delete=models.CASCADE,
    )

    attr_data = GenericRelation("properties.Attribute", related_name="objects")

    @property
    def dbref(self):
        return f"#{self.id}"

    @property
    def objid(self):
        return f"{self.dbref}:{self.generation}"

    def __str__(self):
        return self.name or f"Object {self.objid}"

    def __repr__(self):
        return f"<{self.__class__.__name__} ({self.id}): {self}>"

    @lazy_property
    def attributes(self):
        return AttributeHandler(self)


class Inventory(SharedMemoryModel):
    id = models.OneToOneField(
        ObjectDB,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="inventory_data",
    )
    holder = models.ForeignKey(
        ObjectDB,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="inventory",
    )
    # Special metadata describing how the object is in the inventory.
    # This can be used for things like inventory pockets, or equipment slots.
    data = models.JSONField(blank=False, null=False, default=dict)
