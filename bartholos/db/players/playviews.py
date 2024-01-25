from bartholos.db.players.models import PlayviewDB
from bartholos.db.autoproxy.models import AutoProxyBase
from bartholos.db.players.managers import PlayviewManager
from rich.table import Table
from rich.box import ASCII2
from bartholos.utils.utils import utcnow


class DefaultPlayview(PlayviewDB, metaclass=AutoProxyBase):
    objects = PlayviewManager()

    @classmethod
    def create(cls, obj, user):
        new_play = cls(id=obj, user=user, puppet=obj)
        new_play.save()
        return new_play

    @property
    def options(self):
        return self.user.options

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

    async def uses_screenreader(self) -> bool:
        return await self.user.uses_screenreader()

    async def join_session(self, session):
        if not self.sessions.all():
            # this is the first session.
            await self.at_init_playview(session)
        self.sessions.add(session)
        if self.sessions.count() == 1:
            await self.at_start_playview(session)

    async def at_init_playview(self, session, **kwargs):
        pass

    async def at_start_playview(self, session, **kwargs):
        await self.at_login(**kwargs)

    async def at_login(self, **kwargs):
        await self.record_login()
        await self.unstow()
        await self.announce_join_game()

    async def record_login(self, current_time=None, **kwargs):
        if current_time is None:
            current_time = utcnow()
        p = self.id.playtime
        p.last_login = current_time
        p.save(update_fields=["last_login"])

        ca = p.per_user.get_or_create(user=self.user)[0]
        ca.last_login = current_time
        ca.save(update_fields=["last_login"])

    async def unstow(self):
        from bartholos.db.objects.objects import DefaultObject

        if data := await self.id.attributes.get("location", category="_system"):
            zone_dbref, arbitrary_data = data

            if found := DefaultObject.find_dbref(zone_dbref):
                if zone := found.zone:
                    pass

    async def announce_join_game(self):
        pass
