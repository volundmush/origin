import asyncio
import origin
from origin.utils.utils import utcnow, lazy_property
from .core import DocumentProxy, CollectionManager


class SessionManager(CollectionManager):
    name = "session"
    proxy = "session"


class Session(DocumentProxy):
    @lazy_property
    def sid(self):
        return self.id.split("/", 1)[1]

    async def login(self, user):
        await self.set_field("user", user)
        await origin.PARSERS["main_menu"].start(self)

    async def handle_disconnect(self):
        pass

    async def handle_event(self, event: str, message):
        sess_input = await self.get_field("input", default=list())
        sess_input.append([event, message])
        await self.set_field("input", sess_input)

    async def start(self):
        await origin.PARSERS["login"].start(self)

    async def execute_event(self, event: str, message):
        if func := origin.SERVER_EVENTS.get(event, None):
            await func(self, message)

    async def send_text(self, text: str):
        await self.send_event("Text", {"data": text})

    async def send_gmcp(self, cmd: str, data=None):
        await self.send_event("GMCP", {"cmd": cmd, "data": data})

    async def send_event(self, event: str, data=None):
        await self.sio.emit(event, to=self.sid, data=data)
