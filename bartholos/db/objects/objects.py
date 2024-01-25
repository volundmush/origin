import time
import bartholos
from bartholos.db.objects.models import ObjectDB
from bartholos.db.autoproxy.models import AutoProxyBase
from bartholos.db.objects.managers import ObjectManager
from bartholos.utils.optionhandler import OptionHandler
from bartholos.utils.utils import lazy_property

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

    async def move_to_zone(self, zone, remove_kwargs=None, add_kwargs=None):
        if self.in_zone:
            await self.in_zone.remove_obj(self, **(remove_kwargs or dict()))
        if zone:
            await zone.add_obj(zone, **(add_kwargs or dict()))

    async def get_inventory(self):
        return (x.id for x in self.inventory.all())

    async def get_visible_inventory(self):
        return (x for x in await self.get_inventory() if await self.can_detect(x))

    @property
    def playview(self):
        from bartholos.db.players.playviews import DefaultPlayview

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
            options_dict=bartholos.SETTINGS.OPTIONS_ACCOUNT_DEFAULT,
        )

    async def uses_screenreader(self) -> bool:
        return await self.options.get("screenreader")

    async def rich_table(self, *args, **kwargs) -> Table:
        options = self.options
        real_kwargs = {
            "box": ASCII2,
            "border_style": await options.get("border_style"),
            "header_style": await options.get("header_style"),
            "title_style": await options.get("header_style"),
            "expand": True,
        }
        real_kwargs.update(kwargs)
        if await self.uses_screenreader():
            real_kwargs["box"] = None
        return Table(*args, **real_kwargs)

    async def can_play(self, session) -> bool:
        return True

    async def join_play(self, session):
        from bartholos.db.players.playviews import DefaultPlayview

        if not (play := self.playview):
            play = DefaultPlayview.create(self, session.user)
        await play.join_session(session)

    @property
    def playtime(self):
        from bartholos.db.players.models import CharacterPlaytime

        return CharacterPlaytime.objects.get_or_create(id=self)[0]


class DefaultCharacter(DefaultObject):
    pass


class DefaultPointOfInterest(DefaultObject):
    pass
