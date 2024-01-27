from .core import DocumentProxy, CollectionManager


class LocationManager(CollectionManager):
    name = "location"
    proxy = "location"
    edge = True


class Location(DocumentProxy):
    pass


class InventoryLocation(Location):
    pass


class EquipmentLocation(Location):
    pass


class GridLocation(Location):
    pass
