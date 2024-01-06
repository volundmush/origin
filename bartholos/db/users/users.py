from mudforge.utils import lazy_property
import mudforge

from bartholos.db.users.models import UserDB
from bartholos.db.autoproxy.models import AutoProxyBase
from bartholos.db.users.managers import UserManager
from bartholos.utils.optionhandler import OptionHandler
from bartholos.utils.utils import SessionHandler
from rich.table import Table
from rich.box import ASCII2


class DefaultUser(UserDB, metaclass=AutoProxyBase):
    objects = UserManager()

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

    @lazy_property
    def options(self):
        return OptionHandler(
            self,
            options_dict=mudforge.GAME.settings.OPTIONS_ACCOUNT_DEFAULT,
            savefunc=self.attributes.add,
            loadfunc=self.attributes.get,
            save_kwargs={"category": "option"},
            load_kwargs={"category": "option"},
        )

    async def uses_screenreader(self) -> bool:
        return await self.options.get("screenreader")

    @lazy_property
    def sessions(self):
        return SessionHandler(self)
