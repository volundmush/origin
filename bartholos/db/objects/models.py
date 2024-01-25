from django.db import models
from django.contrib.contenttypes.fields import GenericRelation

from bartholos.db.idmapper.models import SharedMemoryModel
from bartholos.db.autoproxy.models import AutoProxyObject
from bartholos.db.objects.managers import ObjectDBManager

from bartholos.db.properties.attributes import AttributeHandler
from bartholos.utils.utils import lazy_property


class ObjectDB(AutoProxyObject):
    __proxy_family__ = "objects"
    __defaultclasspath__ = "bartholos.db.objects.objects.DefaultObject"
    __applabel__ = "objects"

    objects = ObjectDBManager()

    name = models.CharField(blank=False, null=True, max_length=255)

    lock_data = models.JSONField(blank=False, null=True, default=dict)

    attr_data = GenericRelation("properties.Attribute", related_name="objects")

    @property
    def dbref(self):
        return f"#{self.id}"

    def __str__(self):
        return self.name or f"Object {self.dbref}"

    def __repr__(self):
        return f"<{self.__class__.__name__} ({self.id}): {self}>"

    @lazy_property
    def attributes(self):
        return AttributeHandler(self)
