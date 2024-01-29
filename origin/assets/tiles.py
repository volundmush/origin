class Tile:
    symbol = None

    def __str__(self):
        return self.__class__.__name__


class Void(Tile):
    symbol = "V"


class Road(Tile):
    symbol = "R"
