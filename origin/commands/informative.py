import origin
from .command import Command


class Informative(Command):
    help_category = "Informative"


class Look(Informative):
    """
    Used to look at the surroundings and check things out.
    Can also look at specific targets.

    Usage:
        look [<target>]
    """

    keys = {"look": 1}

    async def func(self):
        if self.args:
            searcher = origin.CLASSES["searcher"](
                self.caller, self.args, allow_self=True
            )
            searcher.add_full(self.caller)

            if not (results := await searcher.search()):
                await self.send_text(f"You can't seem to find a {self.args}.")
                return
            target = results[0]

            await target.render_appearance(self.caller)

        if not (location := await self.caller.get_proxy("location")):
            await self.send_text(f"You are, somehow, nowhere. That's probably bad.")

        await location.render_appearance(self.caller)


COMMANDS = [Look]
