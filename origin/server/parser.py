import origin
from origin.utils.utils import callables_from_module


class SessionParser:
    name = None

    async def parse(self, session, text: str):
        pass

    async def state(self, session) -> dict:
        return await session.get_field("parser_state", default=dict())

    async def set_state(self, session, name, value=None):
        state = await self.state(session)
        if value is None:
            if name in state:
                del state[name]
        else:
            state[name] = value
        await session.set_field("parser_state", state)

    async def close(self, session, replaced=False):
        await session.set_field("parser_state", value=dict())
        if not replaced:
            await session.set_field("parser", value=None)

    async def on_start(self, session):
        pass

    async def start(self, session):
        await session.set_field("parser", self.name)
        await self.on_start(session)
