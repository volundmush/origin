import mudforge
from mudforge.utils import lazy_property
from mudforge.server.game_session import GameSession as BaseGameSession

import bartholos
from bartholos.utils.optionhandler import OptionHandler

from rich.table import Table
from rich.box import ASCII2

from mudforge.game_session import (
    ClientHello,
    ClientCommand,
    ClientUpdate,
    ClientDisconnect,
    ServerDisconnect,
    ServerSendables,
    ServerUserdata,
    Sendable,
    ServerMSSP,
)


class GameSession(BaseGameSession):
    def __init__(self, ws, data):
        super().__init__(ws, data)
        self.user = None
        self.playview = None
        self.parser_stack = list()

    async def handle_priority_py(self, msg: ClientCommand) -> bool:
        parser = mudforge.CLASSES["python_parser"](self)
        await self.add_parser(parser)
        return True

    async def handle_priority_quit(self, msg: ClientCommand) -> bool:
        return True

    async def handle_priority_command(self, msg: ClientCommand) -> bool:
        if self.parser_stack:
            top_parser = self.parser_stack[-1]
            if getattr(top_parser, "priority", False):
                await top_parser.parse(msg.text)
                return True

        if user := self.user:
            if user.is_superuser or user.level >= user.LevelChoices.DEVELOPER:
                lower = msg.text.lower()
                if lower == "_py" or lower.startswith("_py "):
                    return await self.handle_priority_py(msg)

        if msg.text == "QUIT" or msg.text.startswith("QUIT "):
            return await self.handle_priority_quit(msg)

        return False

    async def handle_incoming_command(self, msg: ClientCommand):
        # The IDLE command does nothing.
        if msg.text == "IDLE" or msg.text.startswith("IDLE "):
            return

        # A few special commands like _py and QUIT should be handled with care.
        # Along with Priority Parsers.
        if await self.handle_priority_command(msg):
            return

        # Next we check normal parsers, if they're set.
        if self.parser_stack:
            top_parser = self.parser_stack[-1]
            await top_parser.parse(msg.text)
            return

        if self.playview:
            await self.playview.parse(msg.text)

    async def add_parser(self, parser: "SessionParser"):
        self.parser_stack.append(parser)
        await parser.on_start()

    def send_text(self, text: str):
        out = Sendable()
        out.add_renderable(text)
        msg = ServerSendables()
        msg.add_sendable(out)
        self.outgoing_queue.put_nowait(msg)

    async def start_fresh(self):
        parser_class = mudforge.CLASSES["login_parser"]
        parser = parser_class(self)
        await self.add_parser(parser)

    @property
    def options(self):
        if user := self.user:
            return user.options
        return self._fake_options

    @lazy_property
    def _fake_options(self):
        return OptionHandler(
            self,
            options_dict=mudforge.GAME.settings.OPTIONS_ACCOUNT_DEFAULT,
        )

    async def uses_screenreader(self) -> bool:
        return await self.options.get("screenreader")

    async def rich_table(self, *args, **kwargs) -> Table:
        options = self.options
        real_kwargs = {
            "box": ASCII2,
            "border_style": await options.get("border_style"),
            "header_style": await options.get("header_style"),
            "title_style": await options.get("header_style"),
            "expand": True,
        }
        real_kwargs.update(kwargs)
        if await self.uses_screenreader():
            real_kwargs["box"] = None
        return Table(*args, **real_kwargs)

    async def login(self, user):
        self.user = user
        user.sessions.add(self)

    async def logout(self):
        self.user.sessions.remove(self)
        self.user = None


class SessionParser:
    def __init__(self, session: GameSession, priority: bool = False):
        self.session = session
        self.priority = priority

    async def parse(self, text: str):
        pass

    async def on_close(self):
        pass

    async def close(self):
        await self.on_close()
        if self in self.session.parser_stack:
            self.session.parser_stack.remove(self)

    async def on_start(self):
        pass
