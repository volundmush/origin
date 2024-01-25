import bartholos

from bartholos.utils.utils import callables_from_module


class Core:
    def initialize(self):
        self.import_validatorfuncs()
        self.import_optionclasses()

    def import_validatorfuncs(self):
        for module in bartholos.SETTINGS.VALIDATOR_FUNC_MODULES:
            for k, v in callables_from_module(module).items():
                bartholos.VALIDATORS[k] = v

    def import_optionclasses(self):
        for module in bartholos.SETTINGS.OPTION_CLASS_MODULES:
            for k, v in callables_from_module(module).items():
                bartholos.OPTION_CLASSES[k] = v

    async def run(self):
        pass
