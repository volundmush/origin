import origin
from origin.utils.utils import callables_from_module


class SessionParser:
    def __init__(self, session, priority: bool = False):
        self.session = session
        self.priority = priority

    async def parse(self, text: str):
        pass

    async def on_close(self):
        pass

    async def close(self):
        await self.on_close()
        if self in self.session.parser_stack:
            self.session.parser_stack.remove(self)

    async def on_start(self):
        pass


class Core:
    async def initialize(self):
        self.import_validatorfuncs()
        self.import_optionclasses()

    def import_validatorfuncs(self):
        for module in origin.SETTINGS.VALIDATOR_FUNC_MODULES:
            for k, v in callables_from_module(module).items():
                origin.VALIDATORS[k] = v

    def import_optionclasses(self):
        for module in origin.SETTINGS.OPTION_CLASS_MODULES:
            for k, v in callables_from_module(module).items():
                origin.OPTION_CLASSES[k] = v

    async def run(self):
        pass
