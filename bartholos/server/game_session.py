import asyncio
import bartholos
from bartholos.utils.utils import lazy_property
from bartholos.utils.optionhandler import OptionHandler


class GameSession:
    def __init__(self, sid, sio):
        self.sid = sid
        self.sio = sio
        # This contains arbitrary data sent by the server which will be sent on a reconnect.
        self.outgoing_queue = asyncio.Queue()
        self.parser_stack = list()
        self.user = None
        self.playview = None

    async def handle_disconnect(self):
        pass

    async def handle_event(self, event: str, message):
        match event:
            case "Command":
                await self.handle_incoming_command(
                    message.get("data", "") if message is not None else ""
                )

    async def run(self):
        await self.start()
        while msg := await self.outgoing_queue.get():
            event = msg.get("event", None)
            data = msg.get("data", None)

            if not event:
                continue

            await self.sio.emit(event, to=self.sid, data=data)

    async def start(self):
        await self.start_fresh()

    async def handle_priority_py(self, command: str) -> bool:
        parser = bartholos.CLASSES["python_parser"](self)
        await self.add_parser(parser)
        return True

    async def handle_priority_quit(self, command: str) -> bool:
        return True

    async def handle_priority_command(self, command: str) -> bool:
        if self.parser_stack:
            top_parser = self.parser_stack[-1]
            if getattr(top_parser, "priority", False):
                await top_parser.parse(command)
                return True

        if user := self.user:
            if user.is_superuser or user.level >= user.LevelChoices.DEVELOPER:
                lower = command.lower()
                if lower == "_py" or lower.startswith("_py "):
                    return await self.handle_priority_py(command)

        if command == "QUIT" or command.startswith("QUIT "):
            return await self.handle_priority_quit(command)

        return False

    async def handle_incoming_command(self, command: str):
        # The IDLE command does nothing.
        if command == "IDLE" or command.startswith("IDLE "):
            return

        # A few special commands like _py and QUIT should be handled with care.
        # Along with Priority Parsers.
        if await self.handle_priority_command(command):
            return

        # Next we check normal parsers, if they're set.
        if self.parser_stack:
            top_parser = self.parser_stack[-1]
            await top_parser.parse(command)
            return

        if self.playview:
            await self.playview.parse(command)

    async def add_parser(self, parser: "SessionParser"):
        self.parser_stack.append(parser)
        await parser.on_start()

    def send_text(self, text: str):
        self.send_event("Text", {"data": text})

    def send_gmcp(self, cmd: str, data=None):
        self.send_event("GMCP", {"cmd": cmd, "data": data})

    def send_event(self, event: str, data=None):
        self.outgoing_queue.put_nowait({"event": event, "data": data})

    async def start_fresh(self):
        parser_class = bartholos.CLASSES["login_parser"]
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
            options_dict=bartholos.SETTINGS.OPTIONS_ACCOUNT_DEFAULT,
        )

    async def uses_screenreader(self) -> bool:
        return await self.options.get("screenreader")

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
