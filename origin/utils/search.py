import origin
from enum import IntEnum


class SearchType(IntEnum):
    Inventory = 0
    Equipment = 1
    Location = 2
    World = 3


class Searcher:
    def __init__(
        self,
        caller,
        search_string,
        allow_all=False,
        allow_asterisk=False,
        allow_id=False,
        allow_self=True,
        return_appearance=False,
    ):
        self.caller = caller
        self.search_string = search_string

        # Targets are a sequence of kinds of searches to perform. They will be done in order
        # they are registered.
        self.targets: list[tuple[SearchType, "Object"]] = []

        # Whether to allow all. as a prefix. It's used for filtering.
        self.allow_all = allow_all

        # Whether to allow asterisk (wildcard) as a target, like all.* together
        # means all of anything.
        self.allow_asterisk = allow_asterisk

        # Whether to allow IDs to be used as well as names/keywords.
        self.allow_id = allow_id

        # Whether 'self' or 'me' is allowed.
        self.allow_self = allow_self

        # return an ObjectAppearance instead of an Object wrapper.
        self.return_appearance = return_appearance

    def add_inventory(self, obj):
        self.targets.append((SearchType.Inventory, obj))
        return self

    def add_equipment(self, obj):
        self.targets.append((SearchType.Equipment, obj))
        return self

    def add_location(self, obj):
        self.targets.append((SearchType.Location, obj))
        return self

    def add_world(self, obj):
        self.targets.append((SearchType.World, obj))
        return self

    def add_full(self, obj):
        for method in (self.add_inventory, self.add_equipment, self.add_location):
            method(obj)
        return self

    async def _search_world(self):
        objects = origin.DB.managers["object"]
        async for obj in objects.all_proxy():
            if obj == self.caller:
                continue
            yield obj

    def _search_helper(self, search_type: SearchType, obj: "Object"):
        """
        This should explicitly return an async generator that yields, like
        _search_world just above it.
        """
        match search_type:
            case SearchType.Inventory:
                return obj.inventory()
            case SearchType.Equipment:
                return obj.equipment()
            case SearchType.Location:
                return obj.neighbors()
            case SearchType.World:
                return self._search_world()

    async def search(self) -> list["Object"]:
        counter = 0
        prefix = 1
        target = None

        if "." in self.search_string:
            prefix, target = self.search_string.split(".", 1)
            if prefix.isnumeric():
                prefix = int(prefix)
            else:
                prefix = prefix.lower()
                if prefix == "all":
                    if not self.allow_all:
                        prefix = 1
        else:
            target = self.search_string

        target = target.strip()
        tlower = target.lower()
        if not target:
            return []

        if " " in target:
            target = target.split(" ", 1)[0]

        if target == "*":
            if not self.allow_asterisk:
                return []

        found = []

        if self.allow_self and (target in ("self", "me")):
            if self.return_appearance:
                appearance = await self.caller.get_appearance(self.caller)
                found.append(appearance)
            else:
                found.append(self.caller)
            return found

        for search_type, loc in self.targets:
            async for obj in self._search_helper(search_type, loc):
                appearance = await obj.get_appearance(self.caller)
                added = True if target == "*" else False

                if not added and self.allow_id:
                    added = obj.id == target

                if not added:
                    for keyword in appearance.keywords:
                        if added := keyword.lower().startswith(tlower):
                            break

                if added:
                    counter += 1
                    found.append(appearance if self.return_appearance else obj)

                if prefix != "all" and prefix == counter:
                    return found
        return found
