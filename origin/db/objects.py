from .core import DocumentProxy, CollectionManager


class ObjectManager(CollectionManager):
    name = "object"
    proxy = "object"


class Object(DocumentProxy):
    location_proxy = "location_inventory"

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
                await command.run()

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

    async def can_detect(self, obj: "Object") -> bool:
        return True

    async def can_play(self, session) -> bool:
        return True

    async def join_play(self, session):
        if not (play := await self.get_proxy("playview")):
            playviews = self.dbmanager.managers["playview"]
            user = await session.user()
            data = {"_from": user.id, "_to": self.id}
            play = await playviews.create_document(data=data)
            await self.set_field("playview", play)
        await play.join_session(session)

    async def add_object_location(self, obj: "Object", proxy: str, **kwargs):
        data = {"_from": obj.id, "_to": self.id, "proxy": proxy}
        data.update(kwargs)
        if loc := await obj.get_proxy("location"):
            await obj.putDocument(data=data)
            await loc.change_proxy(proxy, save=False)
            return loc
        else:
            locmgr = self.dbmanager.managers["location"]
            loc = await locmgr.create_document(data=data)
            await obj.set_field("location", loc)
            return loc

    async def add_to_inventory(self, obj: "Object", **kwargs):
        return await self.add_object_location(obj, "inventory_location", **kwargs)

    async def add_to_equipment(self, obj: "Object", **kwargs):
        return await self.add_object_location(obj, "equipment_location", **kwargs)

    async def remove_from_location(self):
        if loc := await self.get_proxy("location"):
            await loc.deleteDocument()
            await self.set_field("location")


class Grid(Object):
    location_proxy = "location_grid"
