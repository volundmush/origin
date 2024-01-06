import mudforge

from mudforge.server.game_session import GameSession as BaseGameSession

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
