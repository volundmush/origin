import os
import django

os.environ["DJANGO_SETTINGS_MODULE"] = "game.django_settings"
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()

import socketio
from sanic import Sanic, response

# from sanic_jwt import Initialize

import bartholos
from bartholos.utils.utils import class_from_module

from game import settings

bartholos.SETTINGS = settings


# Get the absolute path to the 'lib/webroot/' directory
# webroot_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'lib', 'webroot'))

sio = socketio.AsyncServer(async_mode="sanic", namespaces="*")
bartholos.SOCKETIO = sio

app = Sanic(settings.NAME)
bartholos.SANIC = app
# Initialize(app, claim_aud=settings.HOSTNAME, authenticate=account_manager.authenticate, retrieve_user=account_manager.retrieve_user)
sio.attach(app)


# Static file serving
# app.static('/static', os.path.join(webroot_path, 'static'))

for k, v in settings.SERVER_CLASSES.items():
    bartholos.CLASSES[k] = class_from_module(v)

core_class = bartholos.CLASSES["core"]
core = core_class()
bartholos.GAME = core

sess_class = bartholos.CLASSES["game_session"]


# Link in the C++ game library.
@app.before_server_start
def init_game(app, loop):
    core.initialize()


app.add_task(core.run())


@sio.on("connect")
async def connect_handler(sid, environ):
    new_conn = sess_class(sid, sio)
    bartholos.CONNECTIONS[sid] = new_conn
    app.add_task(new_conn.run(), name=f"Connection {sid}")


@sio.on("disconnect")
async def disconnect_handler(sid):
    if conn := bartholos.CONNECTIONS.pop(sid, None):
        await conn.handle_disconnect()
    else:
        print(f"disconnect_handler: No connection for sid {sid}")


@sio.on("*")
async def message_handler(event, sid, message):
    if conn := bartholos.CONNECTIONS.get(sid, None):
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
