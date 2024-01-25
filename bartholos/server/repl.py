import sys

import time
import bartholos
import traceback
from dataclasses import dataclass, field
from rich.highlighter import ReprHighlighter
from rich.text import Text

from aioconsole.console import AsynchronousConsole

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


class PythonParser(SessionParser, AsynchronousConsole):
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

    class FakeStreamWriter:
        def __init__(self, output_callback):
            self.output_callback = output_callback

        async def write(self, data):
            # When something is written, pass it to the output callback
            await self.output_callback(data)

        async def drain(self):
            # Flushing the buffer can be a no-op if there's no actual I/O
            pass

    def __init__(self, session, priority: bool = True):
        SessionParser.__init__(self, session, priority)
        # Create a fake stream writer to handle writes
        self.fake_stream = self.FakeStreamWriter(self.append_output)

        # Initialize AsynchronousConsole with the fake streams
        AsynchronousConsole.__init__(
            self, locals=self.get_locals(), streams=(self.fake_stream, self.fake_stream)
        )
        self.py_buffer = ""

    def get_locals(self) -> dict[str, "any"]:
        return {"self": self.session, "mudforge": mudforge, "bartholos": bartholos}

    def write(self, string):
        """Don't send to stderr, send to self.caller."""
        self.py_buffer += string

    async def append_output(self, data: str):
        self.py_buffer += data

    async def flush(self):
        pass

    async def push(self, line):
        # No need to replace sys.stdout and sys.stderr if we're using fake streams
        try:
            result = await super().push(line)
        except Exception as err:
            await self.handle_output(traceback.format_exc())
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
        results = await self.push(text)
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
