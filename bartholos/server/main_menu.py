from bartholos.utils.utils import partial_match

from .game_session import SessionParser
from bartholos.db.players.playviews import DefaultPlayview
from bartholos.db.players.models import UserOwner
from bartholos.db.objects.objects import DefaultCharacter


class MainMenuParser(SessionParser):
    async def on_start(self):
        await self.render()

    async def render(self):
        user = self.session.user

        sess_table = {"title": "Sessions", "columns": ["ID", "IP", "Client"]}

        rows = list()

        for sess in user.sessions.all():
            # c = sess.capabilities
            rows.append(("Unknwon", "Unknown", "Unknown"))
        sess_table["rows"] = rows
        self.session.send_event("Table", sess_table)

        if owned := user.owned_characters.all():
            char_table = {
                "title": "Characters",
                "columns": [
                    "Name",
                ],
            }
            rows = list()
            for char in owned:
                rows.append((str(char),))
            char_table["rows"] = rows
            self.session.send_event("Table", char_table)

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

        self.session.send_event("Table", cmd_table)

    async def parse(self, text: str):
        text = text.strip()
        if not text:
            await self.render()
            return
        if " " in text:
            text, args = text.split(" ", maxsplit=1)
        else:
            args = ""

        lower = text.lower()

        match lower:
            case "play":
                await self.handle_play(args)
            case "create":
                await self.handle_create(args)
            case "logout":
                await self.handle_logout()

    async def handle_play(self, args: str):
        if not (characters := [x.id for x in self.user.owned_characters.all()]):
            await self.session.send_text("You have no characters!")
            return

        if not args:
            await self.session.send_text("Play which character?")
            return

        if not (found := partial_match(args, characters)):
            await self.session.send_text(
                "That didn't match any of your available characters."
            )
            return

        if not await found.can_play(self.session):
            return

        await self.close()
        await found.join_play(self.session)

    async def handle_create(self, args: str):
        if exists := UserOwner.objects.filter(id__name__iexact=args).first():
            await self.session.send_text(
                "A player character with that name already exists."
            )
            return

        new_char = DefaultCharacter.create(name=args)
        self.user.owned_characters.create(id=new_char)

        await self.render()
        await self.session.send_text(f"Created new character: {new_char}")

    async def handle_logout(self):
        await self.close()
        await self.session.logout()
        await self.session.start_fresh()
