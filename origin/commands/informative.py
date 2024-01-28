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
            pass  # TODO :this

        if not (location := await self.caller.get_proxy("location")):
            await self.caller.send_text(
                f"You are, somehow, nowhere. That's probably bad."
            )

        await location.render_appearance(self.caller)
