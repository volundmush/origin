import time
from django.db import models
from enum import IntEnum

import mudforge
from bartholos.db.autoproxy.models import AutoProxyObject
from bartholos.db.objects.managers import ObjectDBManager


class ObjectDB(AutoProxyObject):
    __proxy_family__ = "objects"
    __defaultclasspath__ = "bartholos.db.objects.objects.DefaultObject"
    __applabel__ = "objects"

    objects = ObjectDBManager()
    generation = models.BigIntegerField(null=False, blank=False, default=lambda: int(time.time()))

    keywords = models.JSONField(blank=False, null=False, default=list)
    name = models.CharField(blank=False, null=True, max_length=255)

    lock_data = models.JSONField(blank=False, null=True, default=dict)

    location = models.ForeignKey("self", null=True, on_delete=models.SET_NULL, blank=False, related_name="contents")
    room = models.ForeignKey("objects.RoomDB", null=True, on_delete=models.SET_NULL, related_name="contents")

    # If location is not null, and room is null, the object is in 'location's inventory.
    # location_meta can specify things like which said inventory.
    location_meta = models.PositiveSmallIntegerField(default=0)


class RoomDB(AutoProxyObject):
    __proxy_family__ = "rooms"
    __defaultclasspath__ = "bartholos.db.objects.rooms.DefaultRoom"
    __applabel__ = "objects"

    objects = RoomDBManager()

    zone = models.ForeignKey(ObjectDB, related_name="rooms", on_delete=models.CASCADE)
    x = models.BigIntegerField(null=False, blank=False, default=0)
    y = models.BigIntegerField(null=False, blank=False, default=0)
    z = models.BigIntegerField(null=False, blank=False, default=0)

    name = models.CharField(blank=False, null=True, max_length=255)

    description = models.TextField(blank=False, null=True)

    class Meta:
        unique_together = (("zone", "x", "y", "z"), )


class Dir(IntEnum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3
    UP = 4
    DOWN = 5
    NORTHWEST = 6
    NORTHEAST = 7
    SOUTHEAST = 8
    SOUTHWEST = 9


class ExitDB(AutoProxyObject):
    __proxy_family__ = "exits"
    __defaultclasspath__ = "bartholos.db.objects.exits.DefaultExit"
    __applabel__ = "objects"

    objects = ExitDBManager()

    room = models.ForeignKey(RoomDB, related_name="exits", on_delete=models.CASCADE)

    class DirectionChoices(models.IntegerChoices):
        NORTH = Dir.NORTH.value
        EAST = Dir.EAST.value
        SOUTH = Dir.SOUTH.value
        WEST = Dir.WEST.value
        UP = Dir.UP.value
        DOWN = Dir.DOWN.value
        NORTHWEST = Dir.NORTHWEST.value
        NORTHEAST = Dir.NORTHEAST.value
        SOUTHEAST = Dir.SOUTHEAST.value
        SOUTHWEST = Dir.SOUTHWEST.value

    direction = models.PositiveSmallIntegerField(choices=DirectionChoices.choices)
