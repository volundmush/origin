from mudforge.utils import classproperty


class Commodity:
    """
    Base class for all Commodities. A Commodity is a lite object where
    the only relevant thing stored in inventory/room is the key and quantity.
    It should be used to represent things which have static/unchanging physical
    properties like weight-per-unit, which cannot be damaged or have other odd state.

    Good examples include gold coins, arrows, unused PokeBalls, low, mid, and high
    healing potions, etc.

    Key items which are held simply to have them, like an id card or random mcguffin,
    also may be good candidates.
    """

    @classproperty
    def name(cls):
        return cls.__name__

    @classproperty
    def plural(cls):
        return f"{cls.name}s"

    @classproperty
    def key(cls):
        """
        The key is a short, preferably lowercase word which is used for
        uniquely identifying this commodity in the commodity dictionary.
        """
        return cls.name

    # weight, in kilograms.
    weight = 0.0

    # volume, in m^3
    volume = 0.0

    def max_stack_size(self, obj) -> int:
        """
        Returns the maximum amount of this that a given object can store.

        This can be used to implement things like wallet sizes, craft material
        bag limits that can be upgraded over time, etc.
        """
        return 9999999999999


class Coin(Commodity):
    pass
