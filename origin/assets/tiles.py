class Tile:
    def __str__(self):
        return self.__class__.__name__


class Void(Tile):
    pass
