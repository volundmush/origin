import origin
from .base import TaskRunner


class SimulationCommands(TaskRunner):
    async def run(self, core, delta_time: float):
        async for (docid, command, proxy) in core.db.query(
            """
            FOR doc IN object
            FILTER COUNT(doc.pending_commands) > 0
            LET command = FIRST(doc.pending_commands)
            UPDATE doc WITH {pending_commands: SHIFT(doc.pending_commands), last_activity: DATE_NOW()} IN object
            RETURN [doc._id, command, doc.proxy]
            """
        ):
            sess = origin.AUTOPROXY[proxy](docid, core.db)
            await sess.execute_command(command)


simulation_commands = SimulationCommands()
