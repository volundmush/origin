import origin
from origin.utils.utils import partial_match

from .parser import SessionParser


class MainMenuParser(SessionParser):
    name = "main_menu"

    async def on_start(self, session):
        await self.render(session)

    async def render(self, session):
        user = await session.get_proxy("user")

        if sessions := [await x.getDocument() async for x in user.sessions()]:
            sess_table = {"title": "Sessions", "columns": ["ID", "IP", "Client"]}
            rows = list()
            for sess in sessions:
                rows.append((sess["_key"], "Unknown", "Unknown"))
            sess_table["rows"] = rows
            await session.send_event("RichTable", sess_table)

        if characters := [await x.getDocument() async for x in user.characters()]:
            char_table = {
                "title": "Characters",
                "columns": [
                    "Name",
                ],
            }
            rows = list()
            for c in characters:
                rows.append([c["name"]])
            char_table["rows"] = rows
            await session.send_event("RichTable", char_table)

        cmd_table = {
            "title": "Commands",
            "columns": ["Command", "Syntax", "Help"],
            "rows": [
                ["play", "play <name>", "Play a character."],
                ["create", "create <name>", "Create new character."],
                ["logout", "logout", "Logout and return to login screen."],
                ["QUIT", "QUIT", "Quit the game."],
            ],
        }

        await session.send_event("RichTable", cmd_table)

    async def parse(self, session, text: str):
        text = text.strip()
        if not text:
            await self.render(session)
            return
        if " " in text:
            text, args = text.split(" ", maxsplit=1)
        else:
            args = ""

        lower = text.lower()

        match lower:
            case "play":
                await self.handle_play(session, args)
            case "create":
                await self.handle_create(session, args)
            case "logout":
                await self.handle_logout(session)

    async def handle_play(self, session, args: str):
        user = await session.get_proxy("user")

        if not (characters := [await x.getDocument() async for x in user.characters()]):
            await session.send_text("You have no characters!")
            return

        if not args:
            await session.send_text("Play which character?")
            return

        if not (found := partial_match(args, characters, key=lambda x: x.get("name"))):
            await session.send_text(
                "That didn't match any of your available characters."
            )
            return

        character = await origin.DB.getProxy(found)

        if not await character.can_play(session):
            return

        await self.close(session)
        await character.join_play(session)

    async def handle_create(self, session, args: str):
        objects = origin.DB.managers["object"]

        name = args.strip()

        if exists := await objects.find_player(name):
            await session.send_text("A player character with that name already exists.")
            return

        user = await session.get_proxy("user")
        data = {"proxy": "player", "name": name, "user": user.id}

        new_char = await objects.create_document(data=data)
        player_start = origin.SETTINGS.PLAYER_START_LOCATION
        start_loc = await origin.DB.getDocument(player_start[0])

        await start_loc.add_object_location(new_char, **player_start[1])

        await self.render(session)
        await session.send_text(f"Created new character: {new_char}")

    async def handle_logout(self, session):
        await self.close(session)
        await session.logout()
        await session.start()
