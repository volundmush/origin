from mudforge.utils import lazy_property

from bartholos.db.users.models import UserDB
from bartholos.db.autoproxy.models import AutoProxyBase
from bartholos.db.users.managers import UserManager
from bartholos.utils.optionhandler import OptionHandler
from rich.table import Table
from rich.box import ASCII2


class DefaultUser(UserDB, metaclass=AutoProxyBase):
    objects = UserManager()

    def rich_table(self, *args, **kwargs) -> Table:
        real_kwargs = {
            "box": ASCII2,
            "border_style": self.options.get("rich_border_style"),
            "header_style": self.options.get("rich_header_style"),
            "title_style": self.options.get("rich_header_style"),
            "expand": True,
        }
        real_kwargs.update(kwargs)
        if self.uses_screenreader():
            real_kwargs["box"] = None
        return Table(*args, **real_kwargs)

    @lazy_property
    def options(self):
        return OptionHandler(
            self,
            options_dict=settings.OPTIONS_ACCOUNT_DEFAULT,
            savefunc=self.attributes.add,
            loadfunc=self.attributes.get,
            save_kwargs={"category": "option"},
            load_kwargs={"category": "option"},
        )
