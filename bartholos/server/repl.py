import sys

import time
import bartholos
import traceback

from aioconsole.console import AsynchronousConsole

from .game_session import SessionParser


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
        return {"self": self.session, "bartholos": bartholos}

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
        self.session.send_event(
            "RichText",
            {"text": "Python REPL Console for Bartholos", "style": "bold green"},
        )
        self.session.send_event(
            "RichText",
            {"text": f"Python {sys.version} on {sys.platform}", "style": "bold green"},
        )
        self.session.send_event(
            "RichText",
            {"text": f"( use quit() to exit )", "style": "bold green"},
        )

    async def on_close(self):
        self.session.send_event(
            "RichText",
            {"text": f"Python Console closed.", "style": "bold green"},
        )

    async def parse(self, text: str):
        if text in ("exit", "exit()", "quit", "quit()", "close", "close()"):
            await self.close()
            return
        if not text:
            return

        self.py_buffer = ""
        self.session.send_event("ReprEcho", {"code": text})

        t0 = time.time()
        results = await self.push(text)
        t1 = time.time()
        self.session.send_event(
            "ReprResult", {"code": self.py_buffer.rstrip(), "runtime": t1 - t0}
        )

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
