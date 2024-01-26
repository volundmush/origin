import asyncio
import origin
from origin.utils.utils import lazy_property
from origin.utils.optionhandler import OptionHandler


class GameSession:
    def __init__(self, sid, sio):
        self.sid = sid
        self.sio = sio
        # This contains arbitrary data sent by the server which will be sent on a reconnect.
        self.outgoing_queue = asyncio.Queue()
        self.parser_stack = list()
        self.user = None
        self.playview = None


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
