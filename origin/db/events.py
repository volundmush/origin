import origin


async def Command(session, message):
    command = message.get("data", "")

    # The IDLE command does nothing.
    if command == "IDLE" or command.startswith("IDLE "):
        return

    # Next we check normal parsers, if they're set.
    if (parser_name := await session.get_field("parser")) and (
        parser := origin.PARSERS.get(parser_name, None)
    ):
        await parser.parse(session, command)
        return

    if pv := await session.get_proxy("playview"):
        await pv.parse(command)
        return

    await session.send_text(f"Oops, cannot handle: {command}")


async def GMCP(session, message):
    pass
