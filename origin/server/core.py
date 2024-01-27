import socketio
import asyncio
import queue
from sanic import Sanic, response
from multiprocessing import Queue

# from sanic_jwt import Initialize

import origin
from origin.utils.utils import class_from_module, callables_from_module


class ServerCore:
    def __init__(self, app: Sanic):
        self.app = app
        sio = socketio.AsyncServer(async_mode="sanic", namespaces="*")
        self.sio = sio
        sio.attach(app)
        app.ctx.socketio = sio
        self.settings = app.ctx.settings

        app.register_listener(self.handle_class_loaders, "before_server_start")
        app.register_listener(self.handle_extra_loaders, "before_server_start")
        app.register_listener(self.setup_db, "before_server_start")
        # app.register_listener(self.handle_task_queue, "before_server_start")

        # app.register_listener(self.setup_shared_ctx, "main_process_start")

        sio.on("*", self.message_handler)
        sio.on("connect", self.connect_handler)
        sio.on("disconnect", self.disconnect_handler)

    async def setup_shared_ctx(self, app):
        app.shared_ctx.tasks_to_run = Queue()
        app.shared_ctx.tasks_completed = Queue()
        asyncio.create_task(self.run_task_queues())

    async def run_task_queues(self):
        tasks = list(origin.TASKS.keys())
        for task in tasks:
            self.app.shared_ctx.tasks_to_run.put(task)

        while True:
            failed = False
            try:
                task = await self.app.shared_ctx.tasks_completed.get_nowait()
                if task is not None:
                    self.app.shared_ctx.tasks_to_run.put_nowait(task)
            except queue.Empty:
                failed = True
            if failed:
                await asyncio.sleep(0.05)

    async def handle_task_queue(self, app, loop):
        while True:
            failed = False
            task = None
            try:
                task = await self.app.shared_ctx.tasks_to_run.get_nowait()
                await self.execute_task(task)
            except queue.Empty:
                failed = True
            finally:
                if task is not None:
                    self.app.shared_ctx.tasks_completed.put_nowait(task)
            if failed:
                await asyncio.sleep(0.05)

    async def execute_task(self, task):
        pass

    def generate_class_loaders(self):
        out = (
            (self.settings.SERVER_CLASSES, origin.CLASSES),
            (self.settings.AUTOPROXY_CLASSES, origin.AUTOPROXY),
            (self.settings.TASKS, origin.TASKS),
            (self.settings.PARSERS, origin.PARSERS),
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

    async def setup_db(self, app, loop):
        settings = self.settings
        db = origin.CLASSES["database"](
            settings.ARANGO_URL,
            settings.ARANGO_DATABASE,
            settings.ARANGO_USERNAME,
            settings.ARANGO_PASSWORD,
        )
        for k, v in settings.COLLECTION_MANAGERS.items():
            db.managers[k] = class_from_module(v)(db)
        self.app.ctx.db = db
        await db.initialize()

    async def connect_handler(self, sid, environ):
        await origin.DB.create_session(sid, environ)

    async def disconnect_handler(self, sid):
        if conn := origin.CONNECTIONS.pop(sid, None):
            await conn.handle_disconnect()
        else:
            print(f"disconnect_handler: No connection for sid {sid}")

    async def message_handler(self, event, sid, message):
        if conn := origin.CONNECTIONS.get(sid, None):
            await conn.handle_event(event, message)
        else:
            print(f"message_handler: No connection for sid {sid}")


def create_application(settings) -> Sanic:
    origin.SETTINGS = settings

    app = Sanic(settings.NAME)

    app.ctx.settings = settings

    core_class = class_from_module(settings.SERVER_CLASSES["core"])
    app.ctx.core = core_class(app)

    # Initialize(app, claim_aud=settings.HOSTNAME, authenticate=account_manager.authenticate, retrieve_user=account_manager.retrieve_user)

    return app
