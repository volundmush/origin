from mudforge.settings_default import *
from collections import defaultdict


SERVER_HOOKS = {"early_launch": ["bartholos.server.hooks.setup_django"]}

SERVER_CLASSES["game_session"] = "bartholos.server.game_session.GameSession"
SERVER_CLASSES["python_parser"] = "bartholos.server.repl.PythonParser"
SERVER_CLASSES["login_parser"] = "bartholos.server.login.LoginParser"
SERVER_CLASSES["main_menu_parser"] = "bartholos.server.main_menu.MainMenuParser"


PROXY_PATHS: dict[str, list[str]] = defaultdict(list)


COMMODITY_CURRENCY_KEY = "coin"


OPTIONS_ACCOUNT_DEFAULT = {
    "border_color": ["Headers, footers, table borders, etc.", "Style", "magenta"],
    "header_star_style": ["* inside Header lines.", "Style", "white"],
    "header_text_style": ["Text inside Header lines.", "Style", "bold white"],
    "header_fill": ["Fill for Header lines.", "Text", "="],
    "separator_star_style": ["* inside Separator lines.", "Style", "white"],
    "separator_text_style": ["Text inside Separator lines.", "Style", "white"],
    "separator_fill": ["Fill for Separator Lines.", "Text", "-"],
    "footer_star_style": ["* inside Footer lines.", "Style", "white"],
    "footer_text_style": ["Text inside Footer Lines.", "Style", "white"],
    "footer_fill": ["Fill for Footer Lines.", "Text", "="],
    "column_names_style": ["Table column header text.", "Style", "green"],
    "timezone": ["Timezone for dates.", "Timezone", "UTC"],
}

# Modules holding Option classes, responsible for serializing the option and
# calling validator functions on it. Same-named functions in modules added
# later in this list will override those added earlier.
OPTION_CLASS_MODULES = ["bartholos.utils.optionclasses"]
# Module holding validator functions. These are used as a resource for
# validating options, but can also be used as input validators in general.
# Same-named functions in modules added later in this list will override those
# added earlier.
VALIDATOR_FUNC_MODULES = ["bartholos.utils.validatorfuncs"]
