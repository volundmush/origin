import bartholos

from bartholos.db.users.models import UserDB
from bartholos.db.autoproxy.models import AutoProxyBase
from bartholos.db.users.managers import UserManager
from bartholos.utils.optionhandler import OptionHandler
from bartholos.utils.utils import SessionHandler, lazy_property


class DefaultUser(UserDB, metaclass=AutoProxyBase):
    objects = UserManager()

    @lazy_property
    def options(self):
        return OptionHandler(
            self,
            options_dict=bartholos.SETTINGS.OPTIONS_ACCOUNT_DEFAULT,
            savefunc=self.attributes.add,
            loadfunc=self.attributes.get,
            save_kwargs={"category": "option"},
            load_kwargs={"category": "option"},
        )

    @lazy_property
    def sessions(self):
        return SessionHandler(self)
