from django.db import models
from bartholos.db.autoproxy.models import AutoProxyObject
from bartholos.db.players.managers import PlayviewDBManager
from django.contrib.contenttypes.fields import GenericRelation
from bartholos.db.properties.attributes import AttributeHandler
from bartholos.utils.utils import SessionHandler, utcnow, lazy_property


class UserPlaytime(models.Model):
    id = models.OneToOneField(
        "users.UserDB",
        primary_key=True,
        related_name="playtime",
        on_delete=models.CASCADE,
    )
    total_playtime = models.PositiveIntegerField(default=0)
    last_login = models.DateTimeField(null=True, blank=True)
    last_logout = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.id)


class CharacterPlaytime(models.Model):
    id = models.OneToOneField(
        "objects.ObjectDB",
        primary_key=True,
        related_name="+",
        on_delete=models.CASCADE,
    )
    total_playtime = models.PositiveIntegerField(default=0)
    last_login = models.DateTimeField(null=True, blank=True)
    last_logout = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.id)


class CharacterAccountPlaytime(models.Model):
    playtime = models.ForeignKey(
        CharacterPlaytime, on_delete=models.CASCADE, related_name="per_user"
    )
    user = models.ForeignKey(
        "users.UserDB",
        on_delete=models.CASCADE,
        related_name="characters_playtime",
    )
    total_playtime = models.PositiveIntegerField(default=0)
    last_login = models.DateTimeField(null=True, blank=True)
    last_logout = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("playtime", "user")


class UserOwner(models.Model):
    id = models.OneToOneField(
        "objects.ObjectDB",
        primary_key=True,
        related_name="user_owner",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        "users.UserDB", related_name="owned_characters", on_delete=models.CASCADE
    )

    def __str__(self):
        return str(self.id)


class PlayviewDB(AutoProxyObject):
    objects = PlayviewDBManager()

    __proxy_family__ = "playviews"
    __defaultclasspath__ = "bartholos.db.players.playview.DefaultPlayview"
    __applabel__ = "players"

    id = models.OneToOneField(
        "objects.ObjectDB",
        primary_key=True,
        related_name="playview",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        "users.UserDB", on_delete=models.CASCADE, related_name="playviews"
    )
    puppet = models.OneToOneField(
        "objects.ObjectDB", related_name="puppeting_playview", on_delete=models.CASCADE
    )

    last_active = models.DateTimeField(null=False, blank=False, default=utcnow)
    date_created = models.DateTimeField(null=False, blank=False, default=utcnow)

    attr_data = GenericRelation("properties.Attribute", related_name="playviews")

    @lazy_property
    def attributes(self):
        return AttributeHandler(self)

    @lazy_property
    def sessions(self):
        return SessionHandler(self)
