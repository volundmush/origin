import origin
from .core import DocumentProxy, CollectionManager


class ObjectManager(CollectionManager):
    name = "object"
    proxy = "object"

    async def find_player(self, name: str):
        async for doc in self.dbmanager.query_proxy(
            """
            FOR doc IN object 
            FILTER LOWER(doc.name) == @name && doc.proxy == "player"
            RETURN doc
            """,
            name=name.strip().lower(),
        ):
            return doc


class ObjectAppearance:
    __slots__ = [
        "id",
        "name",
        "keywords",
        "display_name",
        "description",
        "prefix",
        "pose",
    ]

    def __init__(self, id, name, keywords, display_name, description, prefix, pose):
        self.id = id
        self.name = name
        self.keywords = keywords
        self.display_name = display_name
        self.description = description
        self.prefix = prefix
        self.pose = pose


class Object(DocumentProxy):
    location_proxy = "inventory_location"

    async def weight(self) -> float:
        return 0.0

    async def volume(self) -> float:
        return 0.0

    async def get_appearance(self, viewer) -> ObjectAppearance:
        doc = await self.getDocument()
        name = doc.get("name", None)
        display_name = await self._generate_display_name(viewer, doc)
        prefix = await self._generate_display_prefix(viewer, doc)
        description = await self._generate_description(viewer, doc)
        keywords = await self._generate_keywords(viewer, doc)
        pose = await self._generate_pose(viewer, doc)

        keywords_used = False
        name_used = False

        if not name:
            if keywords:
                name = " ".join(keywords)
            else:
                name = self.id
            keywords_used = True

        if not display_name:
            display_name = name
            name_used = True

        if not keywords_used:
            keywords.extend(name.lower().split())

        if not name_used:
            keywords.extend(display_name.lower().split())

        return ObjectAppearance(
            self.id, name, keywords, display_name, description, prefix, pose
        )

    async def _generate_display_name(self, viewer, doc):
        pass

    async def _generate_display_prefix(self, viewer, doc):
        pass

    async def _generate_description(self, viewer, doc):
        return doc.get("description", "")

    async def _generate_keywords(self, viewer, doc) -> list[str]:
        return list()

    async def _generate_pose(self, viewer, doc):
        pass

    async def execute_command(self, text: str):
        if not (text := text.strip()):
            return
        orig_text = text
        if " " in text:
            text, args = text.split(" ", 1)
        else:
            args = ""
        async for cmd in self.available_commands():
            if res := await cmd.match(self, text):
                command = cmd(self, orig_text, res, args)
                await command.run()

    async def available_commands(self):
        for cmd in await self.sorted_commands():
            if await cmd.available(self):
                yield cmd

    async def sorted_commands(self) -> list["Command"]:
        out = await self.all_commands()
        return sorted(out, key=lambda c: c.priority, reverse=True)

    async def get_basic_commands(self) -> list["Command"]:
        out = list()
        for k, v in origin.COMMAND_SETS.items():
            out.extend(v)

        return out

    async def all_commands(self) -> list["Command"]:
        out = await self.get_basic_commands()

        if loc := await self.get_proxy("location"):
            out.extend(await loc.get_commands(self))

        return list(set(out))

    async def can_detect(self, obj: "Object") -> bool:
        return True

    async def can_play(self, session) -> bool:
        return True

    async def join_play(self, session):
        if not (play := await self.get_proxy("playview")):
            playviews = self.dbmanager.managers["playview"]
            user = await session.get_proxy("user")
            data = {"_from": user.id, "_to": self.id, "_key": self.id.split("/", 1)[1]}
            play = await playviews.create_document(data=data)
        await play.join_session(session)

    async def add_object_location(self, obj: "Object", proxy: str = None, **kwargs):
        data = {
            "_from": obj.id,
            "_to": self.id,
            "proxy": proxy or self.location_proxy,
            "_key": obj.id.split("/", 1)[1],
        }
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

    async def send_text(self, text: str):
        await self.send_event("Text", {"data": text})

    async def send_gmcp(self, cmd: str, data=None):
        await self.send_event("GMCP", {"cmd": cmd, "data": data})

    async def send_event(self, event: str, data=None):
        await self.sio.emit(event, room=self.id, data=data)

    def _contents_helper(self, proxy: str):
        return self.dbmanager.query_proxy(
            """
            FOR doc IN location
            FILTER doc._from == @obj && doc.proxy == @proxy
            return DOCUMENT(doc._to)
            """,
            obj=self.id,
            proxy=proxy,
        )

    async def inventory(self):
        async for doc in self._contents_helper("inventory_location"):
            yield doc

    async def equipment(self):
        async for doc in self._contents_helper("equipment_location"):
            yield doc

    async def contents(self):
        async for doc in self._contents_helper(self.location_proxy):
            yield doc

    async def neighbors(self):
        if loc := await self.get_proxy("location"):
            async for doc in loc.get_neighbors(self):
                yield doc
        else:
            return
            # yes it's unreachable, no dont' remove it.
            yield

    async def render_appearance(self, obj):
        pass

    async def queue_command(self, command: str):
        pending = await self.get_field("pending_commands", list())
        pending.append(command)
        await self.set_field("pending_commands", pending)

    async def queue_commands(self, commands: list[str]):
        pending = await self.get_field("pending_commands", list())
        pending.extend(commands)
        await self.set_field("pending_commands", pending)


class _Character(Object):
    pass


class Player(_Character):
    pass


class NPC(_Character):
    pass


class Grid(Object):
    location_proxy = "grid_location"

    async def get_surroundings(
        self, start: tuple[int, int], abs_x: int = 5, abs_y: int = 7, doc=None
    ):
        if doc is None:
            doc = await self.getDocument()

        start_x, start_y = start
        max_x = start_x + abs(abs_x)
        min_x = start_x - abs(abs_x)
        max_y = start_y + abs(abs_y)
        min_y = start_y - abs(abs_y)

        surroundings = []

        for coordinates, data in doc.get("features", []):
            x, y = coordinates
            if min_x <= x < max_x and min_y <= y < max_y:
                surroundings.append((coordinates, data))

        return surroundings
