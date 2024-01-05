from mudforge.settings_default import *
from collections import defaultdict

SERVER_HOOKS = {
    "early_launch": [
        "bartholos.server.hooks.setup_django"
    ]
}


PROXY_PATHS: dict[str, list[str]] = defaultdict(list)
