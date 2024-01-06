import mudforge

from .game_session import SessionParser
from enum import IntEnum


class LoginStatus(IntEnum):
    USERNAME = 0
    USERNAME_CONFIRM = 1
    WELCOME_PASSWORD = 2
    NEW_PASSWORD = 3
    PASSWORD_CONFIRM = 4


class LoginParser(SessionParser):
    def __init__(self, sess, priority=False):
        super().__init__(sess, priority)
        self.username = None
        self.password = None
        self.user = None
        self.state = LoginStatus.USERNAME

        from bartholos.db.users.users import DefaultUser

        self.users = DefaultUser

        self.state_map = {
            LoginStatus.USERNAME: self.handle_username,
            LoginStatus.USERNAME_CONFIRM: self.handle_username_confirm,
            LoginStatus.WELCOME_PASSWORD: self.handle_welcome_password,
            LoginStatus.PASSWORD_CONFIRM: self.handle_password_confirm,
            LoginStatus.NEW_PASSWORD: self.handle_new_password,
        }

    async def welcome_screen(self):
        self.session.send_text("HELLO WELCOME SCREEN HERE!")

    async def on_start(self):
        await self.welcome_screen()
        await self.render()

    def clear(self):
        self.state = LoginStatus.USERNAME
        self.username = None
        self.password = None
        self.user = None

    async def render(self):
        match self.state:
            case LoginStatus.USERNAME:
                self.session.send_text("Enter Username:")
            case LoginStatus.USERNAME_CONFIRM:
                self.session.send_text(
                    f"You want your Username to be: {self.username}\r\nYes or No (or return):"
                )
            case LoginStatus.WELCOME_PASSWORD:
                self.session.send_text("Password (or return):")
            case LoginStatus.NEW_PASSWORD:
                self.session.send_text(
                    f"Let's set a good password for {self.username}.\r\nPassword (or return):"
                )
            case LoginStatus.PASSWORD_CONFIRM:
                self.session.send_text(
                    f"Enter the password one more time to confirm.\r\nPassword (or return):"
                )

    async def parse(self, text: str):
        if text.lower() == "return":
            self.clear()
            await self.render()
            return

        await self.state_map[self.state](text)
        await self.render()

    async def handle_username(self, text: str):
        text = text.strip()
        if not text:
            return

        self.username = text
        self.user = self.users.objects.filter_family(username__iexact=text).first()
        if self.user:
            self.state = LoginStatus.WELCOME_PASSWORD
        else:
            self.state = LoginStatus.USERNAME_CONFIRM

    async def create_user(self):
        try:
            if not self.users.objects.count():
                self.user = self.users.objects.create_superuser(
                    username=self.username, password=self.password
                )
                self.session.send_text(
                    "FIRST USER TO BE CREATED. THIS USER IS A SUPERUSER."
                )
            else:
                self.user = self.users.objects.create_user(
                    username=self.username, password=self.password
                )
        except Exception as err:
            self.session.send_text(str(err))
            self.clear()

        if self.user:
            await self.login()

    async def on_close(self):
        self.state = None

    async def login(self):
        await self.close()
        await self.session.login(self.user)
        main_menu_parser_class = mudforge.CLASSES["main_menu_parser"]
        main_menu = main_menu_parser_class(self.session)
        await self.session.add_parser(main_menu)

    async def handle_username_confirm(self, text: str):
        text = text.strip().lower()
        if not text:
            return

        match text:
            case "yes":
                self.state = LoginStatus.NEW_PASSWORD
            case "no":
                self.clear()

    async def handle_welcome_password(self, text: str):
        if text.strip() != text:
            self.session.send_text(
                "Passwords may not contain leading or trailing whitespace."
            )
            return
        if self.user.check_password(text):
            await self.login()
        else:
            self.session.send_text("Invalid credentials. Please try again. (or return)")

    async def handle_password_confirm(self, text: str):
        if text.strip() != text:
            self.session.send_text(
                "Passwords may not contain leading or trailing whitespace."
            )
            return

        if self.password != text:
            self.session.send_text("Passwords don't match, try again.")
            self.password = None
            self.state = LoginStatus.NEW_PASSWORD
            return

        await self.create_user()

    async def handle_new_password(self, text: str):
        if text.strip() != text:
            self.session.send_text(
                "Passwords may not contain leading or trailing whitespace."
            )
            return
        self.password = text
        self.state = LoginStatus.PASSWORD_CONFIRM
