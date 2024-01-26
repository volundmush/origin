import os
import socketio
from sanic import Sanic, response

# from sanic_jwt import Initialize

import origin
from origin.utils.utils import class_from_module

from game import settings

origin.SETTINGS = settings


# Get the absolute path to the 'lib/webroot/' directory
# webroot_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'lib', 'webroot'))

sio = socketio.AsyncServer(async_mode="sanic", namespaces="*")
origin.SOCKETIO = sio

app = Sanic(settings.NAME)
origin.SANIC = app
# Initialize(app, claim_aud=settings.HOSTNAME, authenticate=account_manager.authenticate, retrieve_user=account_manager.retrieve_user)
sio.attach(app)


# Static file serving
# app.static('/static', os.path.join(webroot_path, 'static'))

for k, v in settings.SERVER_CLASSES.items():
    origin.CLASSES[k] = class_from_module(v)

origin.DB = origin.CLASSES["database"](
    settings.ARANGO_URL,
    settings.ARANGO_DATABASE,
    settings.ARANGO_USERNAME,
    settings.ARANGO_PASSWORD,
)

for k, v in settings.COLLECTION_MANAGERS.items():
    origin.DB.managers[k] = class_from_module(v)(origin.DB)

for k, v in settings.AUTOPROXY_CLASSES.items():
    origin.AUTOPROXY[k] = class_from_module(v)

core_class = origin.CLASSES["core"]
core = core_class()
origin.GAME = core

sess_class = origin.CLASSES["game_session"]


@app.before_server_start
async def init_db(app, loop):
    await origin.DB.initialize()


@app.before_server_start
async def init_game(app, loop):
    await core.initialize()


app.add_task(core.run())


@sio.on("connect")
async def connect_handler(sid, environ):
    new_conn = sess_class(sid, sio)
    origin.CONNECTIONS[sid] = new_conn
    app.add_task(new_conn.run(), name=f"Connection {sid}")


@sio.on("disconnect")
async def disconnect_handler(sid):
    if conn := origin.CONNECTIONS.pop(sid, None):
        await conn.handle_disconnect()
    else:
        print(f"disconnect_handler: No connection for sid {sid}")


@sio.on("*")
async def message_handler(event, sid, message):
    if conn := origin.CONNECTIONS.get(sid, None):
        await conn.handle_event(event, message)
    else:
        print(f"message_handler: No connection for sid {sid}")


# Finally, run.
# SCREAMING NOTE: DO NOT RUN AS MULTI-PROCESS IT WILL FUCK *EVERYTHING* UP.
if __name__ == "__main__":
    app.run(
        host=settings.SERVER_INTERFACE,
        port=settings.SERVER_PORT,
        single_process=True,
        workers=0,
    )
