import origin

from origin.utils.utils import callables_from_module


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
