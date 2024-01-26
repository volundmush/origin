import time
import origin

from origin.utils.optionhandler import OptionHandler
from origin.utils.utils import lazy_property

from rich.table import Table
from rich.box import ASCII2


class DefaultObject(ObjectDB, metaclass=AutoProxyBase):
    objects = ObjectManager()

    @classmethod
    def create(cls, name: str):
        new_obj = cls(name=name, generation=int(time.time()))
        new_obj.save()
        return new_obj

    def weight(self) -> float:
        return 0.0

    def volume(self) -> float:
        return 0.0

    def get_display_name(self, viewer: "DefaultObject | None" = None) -> str:
        return self.name

    async def execute_cmd(self, text: str):
        if not (text := text.strip()):
            return
        orig_text = text
        if " " in text:
            text, args = text.split(" ", 1)
        else:
            args = ""
        async for cmd in self.available_commands():
            if res := cmd.match(self, text):
                command = cmd(self, orig_text, res, args)
                await cmd.run()

    async def available_commands(self):
        for cmd in await self.sorted_commands():
            if await cmd.available(self):
                yield cmd

    async def sorted_commands(self) -> list["Command"]:
        out = await self.all_commands()
        return sorted(out, key=lambda c: c.priority, reverse=True)

    async def all_commands(self) -> list["Command"]:
        out = list()

        return out

    async def can_detect(self, obj: "DefaultObject") -> bool:
        return True

    @property
    def playview(self):
        from origin.db.players.playviews import DefaultPlayview

        return DefaultPlayview.objects.filter_family(id=self).first()

    @property
    def options(self):
        if play := self.playview:
            return play.options
        return self._fake_options

    @lazy_property
    def _fake_options(self):
        return OptionHandler(
            self,
            options_dict=origin.SETTINGS.OPTIONS_ACCOUNT_DEFAULT,
        )

    async def can_play(self, session) -> bool:
        return True

    async def join_play(self, session):
        from origin.db.players.playviews import DefaultPlayview

        if not (play := self.playview):
            play = DefaultPlayview.create(self, session.user)
        await play.join_session(session)

    @property
    def playtime(self):
        from origin.db.players.models import CharacterPlaytime

        return CharacterPlaytime.objects.get_or_create(id=self)[0]


class DefaultCharacter(DefaultObject):
    pass


class DefaultPointOfInterest(DefaultObject):
    pass
