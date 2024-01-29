from typing import List, Tuple

from .core import DocumentProxy, CollectionManager


class LocationManager(CollectionManager):
    name = "location"
    proxy = "location"
    edge = True


class Location(DocumentProxy):
    proxy_name = "location"

    async def get_neighbors(self, obj):
        """
        This will probably be overloaded and called via super to add more filtering.
        """
        data = await self.getDocument()
        async for doc in self.dbmanager.query_proxy(
            """
            FOR doc IN location
            FILTER doc._to == @loc && doc.proxy == @proxy
            RETURN DOCUMENT(doc._from)
        """,
            loc=data.get("_to"),
            proxy=self.proxy_name,
        ):
            if doc == obj:
                continue
            yield obj

    async def render_appearance(self, obj):
        pass

    async def get_commands(self, obj):
        return list()


class InventoryLocation(Location):
    proxy_name = "inventory_location"


class EquipmentLocation(Location):
    proxy_name = "equipment_location"


class GridLocation(Location):
    proxy_name = "grid_location"

    async def render_appearance(self, obj):
        doc = await self.getDocument()
        grid = await self.get_proxy("_to")
        gdoc = await grid.getDocument()
        message = dict()
        if desc := gdoc.get("grid_description", ""):
            message["grid_description"] = desc
        start = (doc.get("x", 0), doc.get("y", 0))
        surroundings = await grid.get_surroundings(start=start, doc=gdoc)
        message["surroundings"] = surroundings
        await obj.send_event("GridDescription", message)
