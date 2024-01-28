import time
import origin
from .base import TaskRunner


class SessionInput(TaskRunner):
    async def run(self, core, delta_time: float):
        async for (docid, events, proxy) in core.db.query(
            """
            FOR doc IN session
            FILTER COUNT(doc.input) > 0
            LET sess_input = doc.input
            UPDATE doc WITH {input: [], last_activity: DATE_NOW()} IN session
            RETURN [doc._id, sess_input, doc.proxy]
            """
        ):
            sess = origin.AUTOPROXY[proxy](docid, core.db)
            for event, message in events:
                await sess.execute_event(event, message)


session_input = SessionInput()
