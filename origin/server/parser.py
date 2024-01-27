import origin
from origin.utils.utils import callables_from_module


class SessionParser:
    async def parse(self, session, text: str):
        pass

    async def close(self, session, replaced=False):
        if not replaced:
            await session.set_parser(parser=None)

    async def on_start(self, session):
        pass
