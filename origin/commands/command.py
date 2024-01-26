import logging
from mudforge.utils import classproperty

from mudforge.game_session import ServerSendables, Sendable


class Command:
    """
    A Command's docstring is used for its basic help message.
    """

    class CommandException(ValueError):
        pass

    # A command is made of many possible aliases.
    # Each alias can have an optional 'minimum length'
    # needed to match it, for partial matching.
    # The 'first' key is the command's display name.
    keys: dict[str, int | None] = dict()

    # Commands with higher priority will be matched before lower priority.
    priority: int = 0

    help_category: str = "General"
    auto_help: bool = True

    @classproperty
    def name(cls) -> str:
        first_key = next(iter(cls.keys))
        return first_key

    @classmethod
    async def available(cls, obj: "DefaultObject") -> bool:
        """
        Filter available commands. This can be used to restrict
        by permissions, race, whatever.
        """
        return True

    @classmethod
    async def render_help(cls, obj: "DefaultObject" = None) -> str:
        """
        Render the help information for obj.
        """
        return getattr(cls, "__doc__", f"Help not implemented for {cls.name}, sorry.")

    @classmethod
    async def match(cls, obj: "DefaultObject", text: str) -> str | None:
        """
        Iterates through cls.keys and checks if the provided text matches any of them.
        If it does match, it returns the full key.
        If there are no matches, it returns None.

        This will be given just the first typed word, any arguments cut off.
        """
        lower = text.lower()
        for k, v in cls.keys.items():
            key = k.lower()
            if isinstance(v, int):
                minimum = key[:v]
                if minimum.startswith(lower) and key.startswith(lower):
                    return k
            else:
                if key.startswith(lower):
                    return k

        return None

    async def at_pre_cmd(self) -> bool:
        return False

    async def at_post_cmd(self):
        if self.sendables.sendables and (playview := self.playview):
            await playview.send(self.sendables)

    async def run(self):
        try:
            if await self.at_pre_cmd():
                return
            await self.parse()
            await self.func()
        except self.CommandException as err:
            await self.handle_error(err)
        except Exception as err:
            logging.exception(f"Error while executing {self}.")
        finally:
            await self.at_post_cmd()

    async def func(self):
        pass

    async def parse(self):
        """
        This method is used to do pre-parsing of the command's input.
        """

    async def handle_error(self, err: CommandException):
        out = Sendable()
        out.add_renderable(str(err))
        self.sendables.add_sendable(out)

    def __init__(
        self,
        caller: "DefaultObject",
        cmdstring: str,
        match_key: str,
        args: str = "",
        response_id=-1,
    ):
        self.caller = caller
        self.cmdstring = cmdstring
        self.match_key = match_key
        self.args = args
        self.sendables = ServerSendables(response_id=response_id)

    @property
    def playview(self):
        return self.caller.playview
