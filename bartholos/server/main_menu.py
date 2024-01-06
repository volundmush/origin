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

from .game_session import SessionParser


class MainMenuParser(SessionParser):
    async def on_start(self):
        self.session.send_text("Hello World from the main menu!")
