import origin
from passlib.context import CryptContext
from .core import CollectionManager, DocumentProxy

CRYPT_CONTEXT = CryptContext(schemes=["argon2"], deprecated="auto")


class UserManager(CollectionManager):
    name = "user"
    proxy = "user"

    async def find_user(self, username: str):
        async for doc in self.dbmanager.query_proxy(
            "FOR doc IN user FILTER LOWER(doc.username) == @username RETURN doc",
            username=username.lower(),
        ):
            return doc

    async def create_user(self, username: str, password: str, key=None):
        if await self.find_user(username):
            raise ValueError(f"User {username} already exists.")
        try:
            password_hash = CRYPT_CONTEXT.hash(password)
        except (TypeError, ValueError):
            raise ValueError(f"Non-hashable password, try another.")
        data = {"username": username, "password_hash": password_hash}
        return await self.create_document(data, key=key)


class User(DocumentProxy):
    async def characters(self):
        async for doc in self.dbmanager.query_proxy(
            "FOR doc IN object FILTER doc.user == @user RETURN doc", user=self.id
        ):
            yield doc

    async def sessions(self):
        async for doc in self.dbmanager.query_proxy(
            "FOR doc IN session FILTER doc.user == @user RETURN doc", user=self.id
        ):
            if found := origin.CONNECTIONS.get(doc.sid, None):
                yield found
            else:
                origin.CONNECTIONS[doc.sid] = doc
                yield doc

    async def playviews(self):
        async for doc in self.dbmanager.query_proxy(
            "FOR doc IN playview FILTER doc._from == @user RETURN doc", user=self.id
        ):
            yield doc

    async def authenticate(self, password: str) -> bool:
        doc = await self.getDocument()
        if not (password_hash := doc.get("password_hash", None)):
            return False
        return CRYPT_CONTEXT.verify(password, password_hash)

    async def set_password(self, password: str):
        data = {"password_hash": CRYPT_CONTEXT.hash(password) if password else None}
        params = {"keepNull": "false"}
        await self.patchDocument(data, params=params)

    async def level(self) -> int:
        doc = await self.getDocument()
        return doc.get("level", 0)
