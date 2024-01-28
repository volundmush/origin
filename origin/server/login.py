import origin

from .parser import SessionParser
from enum import IntEnum


class LoginParser(SessionParser):
    name = "login"

    async def welcome_screen(self, session):
        await session.send_text("HELLO WELCOME SCREEN HERE!")

    async def on_start(self, session):
        await self.welcome_screen(session)
        await self.render(session)

    async def clear(self, session):
        await session.set_field("parser_state", value={"state": "username"})

    async def render(self, session):
        state = await self.state(session)
        match state.get("state", "username"):
            case "username":
                await session.send_text("Enter Username:")
            case "username_confirm":
                await session.send_text(
                    f"You want your Username to be: {state.get('username')}\r\nYes or No (or return):"
                )
            case "welcome":
                await session.send_text("Password (or return):")
            case "password":
                await session.send_text(
                    f"Let's set a good password for {state.get('username')}.\r\nPassword (or return):"
                )
            case "password_confirm":
                await session.send_text(
                    f"Enter the password one more time to confirm.\r\nPassword (or return):"
                )

    async def parse(self, session, text: str):
        if text.lower() == "return":
            await self.clear(session)
            await self.render(session)
            return

        state = await self.state(session)
        match state.get("state", "username"):
            case "username":
                await self.handle_username(session, text)
            case "username_confirm":
                await self.handle_username_confirm(session, text)
            case "welcome":
                await self.handle_welcome_password(session, text)
            case "password":
                await self.handle_new_password(session, text)
            case "password_confirm":
                await self.handle_password_confirm(session, text)

    async def handle_username(self, session, text: str):
        text = text.strip()
        if not text:
            return

        users = origin.DB.managers["user"]
        if user := await users.find_user(text):
            await self.set_state(session, "user", user.id)
            await self.set_state(session, "state", value="welcome")
        else:
            await self.set_state(session, "username_confirm")
        await self.render(session)

    async def create_user(self, session):
        users = origin.DB.managers["user"]
        count = await users.count()
        state = await self.state(session)
        user = None
        try:
            data = {
                "username": state.get("username"),
                "password": state.get("password"),
            }
            if not count:
                data["level"] = 5

            user = await users.create_user(**data)
            if not count:
                session.send_text("FIRST USER TO BE CREATED. THIS USER IS A SUPERUSER.")
        except Exception as err:
            await session.send_text(str(err))
            await self.clear(session)

        if user:
            await self.login(session, user)
        else:
            await self.render(session)

    async def login(self, session, user):
        await self.close(session)
        await session.login(user)

    async def handle_username_confirm(self, session, text: str):
        text = text.strip().lower()
        if not text:
            return

        match text:
            case "yes":
                await self.set_state(session, "state", "password")
            case "no":
                await self.clear(session)
            case _:
                await session.send_text("What? Try again...")
        await self.render(session)

    async def handle_welcome_password(self, session, text: str):
        if text.strip() != text:
            await session.send_text(
                "Passwords may not contain leading or trailing whitespace."
            )
            return

        state = await self.state(session)

        user = await origin.DB.getDocument(state.get("user"))

        if await user.authenticate(text):
            await self.login(session, user)
        else:
            await session.send_text(
                "Invalid credentials. Please try again. (or return)"
            )
            await self.render(session)

    async def handle_password_confirm(self, session, text: str):
        if text.strip() != text:
            await session.send_text(
                "Passwords may not contain leading or trailing whitespace."
            )
            return

        state = await self.state(session)
        password = state.get("password")

        if password != text:
            await session.send_text("Passwords don't match, try again.")
            await self.set_state(session, "password", value=None)
            await self.set_state(session, "state", "password")
            return

        await self.create_user(session)

    async def handle_new_password(self, session, text: str):
        if text.strip() != text:
            await session.send_text(
                "Passwords may not contain leading or trailing whitespace."
            )
            return
        await self.set_state(session, "state", "password_confirm")
        await self.set_state(session, "password", text)
        await self.render(session)
