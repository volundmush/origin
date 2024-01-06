from bartholos.db.zones.models import ZoneDB
from bartholos.db.autoproxy.models import AutoProxyBase
from bartholos.db.zones.managers import ZoneManager

from mudforge.game_session import ServerSendables, Sendable


class DefaultZone(ZoneDB, metaclass=AutoProxyBase):
    objects = ZoneManager()

    async def get_neighbors(self, obj: "DefaultObject") -> list["DefaultObject"]:
        return list(self.contents.all().exclude(id=obj))

    async def get_visible_neighbors(
        self, obj: "DefaultObject"
    ) -> list["DefaultObject"]:
        out = await self.get_neighbors(obj)

        return [o for o in out if await obj.can_detect(o)]

    async def render_location(self, obj: "DefaultObject"):
        # No reason to render for something that's not listening.
        if not (play := obj.playview):
            return

        sendables = ServerSendables()

        for method in [
            self.render_location_header,
            self.render_location_description,
            self.render_location_contents,
        ]:
            await method(obj, sendables)

        if sendables.sendables:
            await play.send(sendables)

    separator = (
        "O----------------------------------------------------------------------O"
    )

    async def render_location_header(self, obj, sendables: ServerSendables):
        pass

    async def render_location_description(self, obj, sendables: ServerSendables):
        pass

    async def render_location_contents(self, obj, sendables: ServerSendables):
        neighbors = await self.get_visible_neighbors(obj)

    async def get_commands(self, obj) -> list["Command"]:
        return list()

    async def remove_obj(self, obj, **kwargs):
        obj.in_zone = None
        obj.save(update_fields=["in_zone"])

    async def add_obj(self, obj, **kwargs):
        obj.in_zone = self
        obj.save(update_fields=["in_zone"])
