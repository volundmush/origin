import sys
import code
import time
import mudforge
import bartholos
import traceback
from dataclasses import dataclass, field
from rich.highlighter import ReprHighlighter
from rich.text import Text

from mudforge.game_session import (
    ClientHello,
    ClientCommand,
    ClientUpdate,
    ClientDisconnect,
    ServerDisconnect,
    ServerSendables,
    ServerUserdata,
    Sendable,
    ServerMSSP,
)

from .game_session import SessionParser


@dataclass
class PythonRepresentation:
    data: str
    runtime: float | None = None
    prefix: str | None = None

    async def at_portal_receive(self, sess):
        rendered = sess.console.render_str(
            self.data,
            markup=False,
            highlight=True,
            highlighter=ReprHighlighter(),
        )

        sess.console.print(rendered)
        rendered = sess.console.export_text(clear=True, styles=True).rstrip()

        if self.prefix:
            out = f"{self.prefix} {rendered}"
        else:
            out = rendered

        if self.runtime:
            out += f"\r\n ( runtime ~ {(self.runtime * 1000):.4f}ms )"

        await sess.send_text(out)


class PythonParser(SessionParser, code.InteractiveConsole):
    """
    Implements a Python REPL interpreter for developers.
    Based on Evennia's own rendition.
    """

    class FakeStd:
        def __init__(self, parser, session):
            self.parser = parser
            self.session = session

        def write(self, string):
            self.parser.py_buffer += string

    def __init__(self, session, priority: bool = True):
        SessionParser.__init__(self, session, priority)
        code.InteractiveConsole.__init__(self, locals=self.get_locals())
        self.fake_std = self.FakeStd(self, session)
        self.py_buffer = ""

    def get_locals(self) -> dict[str, "any"]:
        return {"self": self.session, "mudforge": mudforge, "bartholos": bartholos}

    def write(self, string):
        """Don't send to stderr, send to self.caller."""
        self.py_buffer += string

    def push(self, line):
        """Push some code, whether complete or not."""
        old_stdout = sys.stdout
        old_stderr = sys.stderr

        sys.stdout = self.fake_std
        sys.stderr = self.fake_std
        result = None

        try:
            result = super().push(line)
        except Exception as err:
            self.write(traceback.format_exc())
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        return result

    async def on_start(self):
        out = Sendable()
        out.add_renderable(
            Text("Python REPL Console for Bartholos", style="bold green")
        )
        out.add_renderable(
            Text(f"Python {sys.version} on {sys.platform}", style="bold green")
        )
        out.add_renderable(Text(f"( use quit() to exit )", style="bold green"))
        msg = ServerSendables()
        msg.add_sendable(out)
        await self.session.outgoing_queue.put(msg)

    async def on_close(self):
        out = Sendable()
        out.add_renderable(Text("Python Console closed.", style="bold green"))
        msg = ServerSendables()
        msg.add_sendable(out)
        await self.session.outgoing_queue.put(msg)

    async def parse(self, text: str):
        if text in ("exit", "exit()", "quit", "quit()", "close", "close()"):
            await self.close()
            return
        if not text:
            return

        self.py_buffer = ""
        out = PythonRepresentation(text, prefix=">>>")
        await self.session.outgoing_queue.put(out)
        t0 = time.time()
        results = self.push(text)
        t1 = time.time()
        out = PythonRepresentation(self.py_buffer.rstrip(), runtime=t1 - t0)
        await self.session.outgoing_queue.put(out)

    def showtraceback(self):
        """Display the exception that just occurred.

        We remove the first stack item because it is our own code.

        The output is written by self.write(), below.

        """
        sys.last_type, sys.last_value, last_tb = ei = sys.exc_info()
        sys.last_traceback = last_tb
        sys.last_exc = ei[1]
        try:
            lines = traceback.format_exception(ei[0], ei[1], last_tb.tb_next)
            self.write("".join(lines))
        finally:
            last_tb = ei = None
