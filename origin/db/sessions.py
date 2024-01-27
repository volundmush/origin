import asyncio
import origin
from origin.utils.utils import utcnow, lazy_property
from .core import DocumentProxy, CollectionManager


class SessionManager(CollectionManager):
    name = "session"
    proxy = "session"


class Session(DocumentProxy):
    @property
    def sio(self):
        return origin.SOCKETIO

    @lazy_property
    def sid(self):
        return self.id.split("/", 1)[1]

    async def login(self, user):
        await self.set_field("user", user)
        await origin.PARSERS["main_menu"].start(self)

    async def handle_disconnect(self):
        pass

    async def handle_event(self, event: str, message):
        match event:
            case "Command":
                await self.handle_incoming_command(
                    message.get("data", "") if message is not None else ""
                )

    async def start(self):
        await origin.PARSERS["login"].start(self)

    async def handle_priority_quit(self, command: str) -> bool:
        return True

    async def handle_priority_command(self, command: str) -> bool:
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
        if (parser_name := await self.get_field("parser")) and (
            parser := origin.PARSERS.get(parser_name, None)
        ):
            await parser.parse(self, command)
            return

        if pv := await self.get_proxy("playview"):
            await pv.parse(command)
            return

        await self.send_text(f"Oops, cannot handle: {command}")

    async def send_text(self, text: str):
        await self.send_event("Text", {"data": text})

    async def send_gmcp(self, cmd: str, data=None):
        await self.send_event("GMCP", {"cmd": cmd, "data": data})

    async def send_event(self, event: str, data=None):
        await self.sio.emit(event, to=self.sid, data=data)
