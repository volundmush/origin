from bartholos.db.objects.models import ObjectDB
from bartholos.db.autoproxy.models import AutoProxyBase
from bartholos.db.objects.managers import ObjectManager


class DefaultObject(ObjectDB, metaclass=AutoProxyBase):
    objects = ObjectManager()

    @property
    def zone(self) -> "DefaultZone | None":
        from bartholos.db.zones.zones import DefaultZone

        return DefaultZone.objects.filter(id=self).first()

    def weight(self) -> float:
        return 0.0

    def volume(self) -> float:
        return 0.0

    def get_display_name(self, viewer: "DefaultObject | None" = None) -> str:
        return self.name

    async def execute_cmd(self, text: str):
        if not (text := text.strip()):
            return
        orig_text = text
        if " " in text:
            text, args = text.split(" ", 1)
        else:
            args = ""
        async for cmd in self.available_commands():
            if res := cmd.match(self, text):
                command = cmd(self, orig_text, res, args)
                await cmd.run()

    async def available_commands(self):
        for cmd in await self.sorted_commands():
            if await cmd.available(self):
                yield cmd

    async def sorted_commands(self) -> list["Command"]:
        out = await self.all_commands()
        return sorted(out, key=lambda c: c.priority, reverse=True)

    async def all_commands(self) -> list["Command"]:
        out = list()

        return out

    async def can_detect(self, obj: "DefaultObject") -> bool:
        return True

    async def move_to_zone(self, zone, remove_kwargs=None, add_kwargs=None):
        if self.in_zone:
            await self.in_zone.remove_obj(self, **(remove_kwargs or dict()))
        if zone:
            await zone.add_obj(zone, **(add_kwargs or dict()))

    async def get_inventory(self):
        return (x.id for x in self.inventory.all())

    async def get_visible_inventory(self):
        return (x for x in await self.get_inventory() if await self.can_detect(x))


class DefaultCharacter(DefaultObject):
    pass


class DefaultPointOfInterest(DefaultObject):
    pass
