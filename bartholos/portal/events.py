async def Text(session, event: str, data):
    if (txt := data.get("data", None)) is not None:
        await session.send_game_text(txt)


async def GMCP(session, event: str, data):
    cmd = data.get("cmd", None)
    data = data.get("data", dict())
    await session.send_gmcp(cmd, data)


async def Table(session, event: str, data):
    args = list()
    if columns := data.pop("columns", None):
        args = columns

    kwargs = dict()

    rows = data.pop("rows", list())

    kwargs.update(data)

    table = await session.rich_table(*args, **kwargs)

    for row in rows:
        table.add_row(*row)

    rendered = session.print(table)
    await session.send_game_text(rendered)
