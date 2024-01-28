import socketio
import asyncio
import queue
import time
from sanic import Sanic, response
from multiprocessing import Queue

# from sanic_jwt import Initialize

import origin
from origin.utils.utils import class_from_module, callables_from_module


class GameTask:
    __slots__ = ["name", "interval", "countdown", "function"]

    def __init__(self, name: str, interval: float, function):
        self.name = name
        self.interval = interval
        self.countdown = interval
        self.function = function

    async def update(self, core, delta_time: float):
        self.countdown -= delta_time
        if self.countdown <= 0:
            task_delta = self.interval + abs(self.countdown)
            await self.function(core, task_delta)
            self.countdown += self.interval


class ServerCore:
    def __init__(self, app: Sanic):
        self.app = app
        sio = socketio.AsyncServer(async_mode="sanic", namespaces="*")
        origin.SOCKETIO = sio
        self.sio = sio
        sio.attach(app)
        app.ctx.socketio = sio
        self.settings = app.ctx.settings
        self.tasks = list()
        self.db = None

        # app.register_listener(self.setup_shared_ctx, "before_server_start")

        app.register_listener(self.handle_class_loaders, "before_server_start")
        app.register_listener(self.handle_extra_loaders, "before_server_start")
        app.register_listener(self.setup_db, "before_server_start")
        app.register_listener(self.setup_tasks, "before_server_start")

        # app.register_listener(self.handle_task_queue, "before_server_start")

        sio.on("*", self.message_handler)
        sio.on("connect", self.connect_handler)
        sio.on("disconnect", self.disconnect_handler)

    async def setup_shared_ctx(self, app):
        app.shared_ctx.tasks_to_run = Queue()
        tasks = list(self.settings.TASKS.keys())
        for task in tasks:
            app.shared_ctx.tasks_to_run.put_nowait(task)

    async def handle_task_queue(self, app, loop):
        app.add_task(self.execute_task_queue)

    async def execute_task_queue(self):
        while True:
            failed = False
            task = None
            try:
                task = self.app.shared_ctx.tasks_to_run.get_nowait()
                await self.execute_task(task)
            except queue.Empty:
                failed = True
            except Exception as err:
                print(f"Yeah this ain't good: {err}")
                failed = True
            finally:
                if task is not None:
                    self.app.shared_ctx.tasks_to_run.put_nowait(task)
            if failed:
                await asyncio.sleep(0.05)

    async def execute_task(self, task):
        if func := origin.TASKS.get(task):
            await func(self)

    def generate_class_loaders(self):
        out = (
            (self.settings.SERVER_CLASSES, origin.CLASSES),
            (self.settings.AUTOPROXY_CLASSES, origin.AUTOPROXY),
        )
        return out

    async def handle_class_loaders(self, app, loop):
        for source, destination in self.generate_class_loaders():
            for k, v in source.items():
                destination[k] = class_from_module(v)

    async def handle_extra_loaders(self, app, loop):
        for module in self.settings.TILE_MODULES:
            for k, v in callables_from_module(module).items():
                tile = v()
                origin.TILES[str(tile)] = tile

        for module in self.settings.SERVER_EVENT_HANDLER_MODULES:
            for k, v in callables_from_module(module).items():
                origin.SERVER_EVENTS[k] = v

        for k, v in self.settings.PARSERS.items():
            origin.PARSERS[k] = class_from_module(v)()

    async def setup_db(self, app, loop):
        settings = self.settings
        db = origin.CLASSES["database"](
            settings.ARANGO_URL,
            settings.ARANGO_DATABASE,
            settings.ARANGO_USERNAME,
            settings.ARANGO_PASSWORD,
        )
        self.db = db
        origin.DB = db
        for k, v in settings.COLLECTION_MANAGERS.items():
            db.managers[k] = class_from_module(v)(db)
        self.app.ctx.db = db
        await db.initialize()

    async def setup_tasks(self, app, loop):
        for k, v in self.settings.TASKS.items():
            interval = v.get("interval", 0.0)
            path = v.get("path")
            func = class_from_module(path)
            gtask = GameTask(k, interval, func)
            self.tasks.append(gtask)
        app.add_task(self.run_game)

    async def run_game(self):
        delta_time = 0.1
        frequency = 0.1

        while True:
            start = time.perf_counter()
            await self.run_tasks(delta_time)
            end = time.perf_counter()

            duration = end - start

            remaining = frequency - duration

            if remaining > 0:
                await asyncio.sleep(remaining)

            now = time.perf_counter()
            delta_time = now - start

    async def run_tasks(self, delta_time: float):
        for task in self.tasks:
            await task.update(self, delta_time)

    async def connect_handler(self, sid, environ):
        sess_manager = self.db.managers["session"]
        sess = await sess_manager.create_document(data=dict(), key=sid)
        await sess.start()

    async def disconnect_handler(self, sid):
        if sess := await self.db.getDocument(f"session/{sid}"):
            await sess.handle_disconnect()

    async def message_handler(self, event, sid, message):
        sess_manager = self.db.managers["session"]
        if sess := await self.db.getDocument(f"session/{sid}"):
            await sess.handle_event(event, message)


def create_application(settings) -> Sanic:
    origin.SETTINGS = settings

    app = Sanic(settings.NAME)

    app.ctx.settings = settings

    core_class = class_from_module(settings.SERVER_CLASSES["core"])
    app.ctx.core = core_class(app)

    # Initialize(app, claim_aud=settings.HOSTNAME, authenticate=account_manager.authenticate, retrieve_user=account_manager.retrieve_user)

    return app
