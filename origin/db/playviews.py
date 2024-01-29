from origin.utils.utils import lazy_property
from .core import DocumentProxy, CollectionManager


class PlayviewManager(CollectionManager):
    name = "playview"
    edge = True
    proxy = "playview"


class Playview(DocumentProxy):
    def __init__(self, id, dbmanager):
        super().__init__(id, dbmanager)

    @lazy_property
    def room(self):
        return f"object/{self.id.split('/',1)[1]}"

    async def sessions(self):
        async for doc in self.dbmanager.query_proxy(
            "FOR doc IN session FILTER doc.playview == @pv RETURN doc", pv=self.id
        ):
            yield doc

    async def join_session(self, session):
        await session.set_field("playview", self)
        await self.sio.enter_room(session.sid, self.room)
        sessions = [sess async for sess in self.sessions()]
        if len(sessions) == 1:
            await self.at_start_playview(session)
        await self.at_session_join(session)

    async def at_session_join(self, session, **kwargs):
        pass

    async def at_start_playview(self, session, **kwargs):
        await self.at_login(**kwargs)

    async def at_login(self, **kwargs):
        await self.record_login()
        await self.unstow()
        await self.announce_join_game()

    async def record_login(self, current_time=None, **kwargs):
        pass

    async def unstow(self):
        pass

    async def announce_join_game(self):
        pass

    async def send_text(self, text: str):
        await self.send_event("Text", {"data": text})

    async def send_gmcp(self, cmd: str, data=None):
        await self.send_event("GMCP", {"cmd": cmd, "data": data})

    async def send_event(self, event: str, data=None):
        await self.sio.emit(event, room=self.room, data=data)

    async def parse(self, command: str):
        """
        Later this might handle an aliasing system, or some parsers,
        but for now it just forwards the command.
        """
        obj = await self.get_proxy("_to")
        await obj.queue_command(command)
