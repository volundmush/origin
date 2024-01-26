import asyncio
import origin
from origin.utils.utils import utcnow, lazy_property
from origin.utils.optionhandler import OptionHandler
from .core import DocumentProxy, CollectionManager


class SessionManager(CollectionManager):
    name = "session"
    proxy = "session"


class Session(DocumentProxy):
    def __init__(self, id: str, dbmanager):
        super().__init__(id, dbmanager)
        self.parser_stack = list()

    @property
    def sio(self):
        return origin.SOCKETIO

    @lazy_property
    def sid(self):
        return self.id.split("/", 1)[1]

    async def user(self):
        doc = await self.getDocument()
        if u := doc.get("user", None):
            return await self.dbmanager.getDocument(u)

    async def playview(self):
        doc = await self.getDocument()
        if v := doc.get("playview", None):
            return await self.dbmanager.getDocument(v)

    async def set_user(self, user: str):
        data = {"user": user}
        params = {"keepNull": "false"}
        await self.patchDocument(data, params=params)

    async def login(self, user):
        await self.set_user(user.id)

    async def set_playview(self, playview: str):
        data = {"playview": playview}
        params = {"keepNull": "false"}
        await self.patchDocument(data, params=params)

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

    async def start(self):
        await self.start_fresh()

    async def handle_priority_py(self, command: str) -> bool:
        parser = origin.CLASSES["python_parser"](self)
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

        if user := await self.user():
            level = await user.level()
            if level >= 5:
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

        if pv := await self.playview():
            await pv.parse(command)

    async def add_parser(self, parser: "SessionParser"):
        self.parser_stack.append(parser)
        await parser.on_start()

    async def send_text(self, text: str):
        await self.send_event("Text", {"data": text})

    async def send_gmcp(self, cmd: str, data=None):
        await self.send_event("GMCP", {"cmd": cmd, "data": data})

    async def send_event(self, event: str, data=None):
        await self.sio.emit(event, to=self.sid, data=data)

    async def start_fresh(self):
        parser_class = origin.CLASSES["login_parser"]
        parser = parser_class(self)
        await self.add_parser(parser)
