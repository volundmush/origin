from rich.highlighter import ReprHighlighter
from rich.text import Text as RealRichText


async def RichText(session, event: str, data):
    if (txt := data.pop("text", None)) is not None:
        text = RealRichText(txt, **data)
        rendered = session.print(text)
        await session.send_text(rendered)


async def Text(session, event: str, data):
    if (txt := data.get("data", None)) is not None:
        await session.send_game_text(txt)


async def GMCP(session, event: str, data):
    cmd = data.get("cmd", None)
    data = data.get("data", dict())
    await session.send_gmcp(cmd, data)


async def RichTable(session, event: str, data):
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


async def ReprEcho(session, event: str, data):
    code = data.get("code", "")
    highlighted = session.console.render_str(
        code,
        markup=False,
        highlight=True,
        highlighter=ReprHighlighter(),
    )

    rendered = session.print(highlighted)

    rendered = f">>> {rendered}"

    await session.send_text(rendered)


async def ReprResult(session, event: str, data):
    code = data.get("code", "")
    highlighted = session.console.render_str(
        code,
        markup=False,
        highlight=True,
        highlighter=ReprHighlighter(),
    )

    rendered = session.print(highlighted)

    rendered = f"<<< {rendered}"

    if runtime := data.get("runtime", None):
        rendered += f"\r\n ( runtime ~ {(runtime * 1000):.4f}ms )"

    await session.send_text(rendered)
