#!/usr/bin/env python


def run(name: str):
    import os
    import bartholos
    from bartholos.utils.utils import class_from_module

    from game import settings

    bartholos.SETTINGS = settings

    for k, v in settings.PORTAL_CLASSES.items():
        bartholos.CLASSES[k] = class_from_module(v)

    core_class = bartholos.CLASSES["core"]

    pidfile = f"{name}.pid"

    with open(pidfile, "w") as pid_f:
        pid_f.write(str(os.getpid()))
        pid_f.flush()

        try:
            app = core_class(settings)
            bartholos.GAME = app
            app.run()
        except Exception as err:
            print(str(err))
    os.remove(pidfile)


if __name__ == "__main__":
    run("portal")
