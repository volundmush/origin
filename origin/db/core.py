import httpx
import asyncio
import origin
import jwt
import time


class Cursor:
    def __init__(self, data: dict, dbmanager):
        self.id = data.get("id")
        self.data = data
        self.dbmanager = dbmanager

    def count(self) -> int:
        return len(self.data.get("result", list()))

    async def fetch_next_batch(self) -> bool:
        next_batch_id = self.data.get("nextBatchId")
        if next_batch_id:
            result = await self.dbmanager.post(f"/_api/cursor/{self.id}")
            if result.status_code == 200:
                self.data = result.json()
                return True
            else:
                self.data = None
                return False

    async def results(self):
        while True:
            for item in self.data.get("result", []):
                yield item

            if "nextBatchId" in self.data:
                if not await self.fetch_next_batch():
                    break
            else:
                break

    async def close(self):
        await self.dbmanager.delete(f"/_api/cursor/{self.id}")


class DatabaseManager:
    class DatabaseException(ValueError):
        pass

    def __init__(self, base_url: str, dbname: str, username: str, password: str):
        self.dbname = dbname
        self.username = username
        self.password = password
        self.managers = dict()
        self.client = httpx.AsyncClient(base_url=base_url, http2=True)
        self.dbclient = httpx.AsyncClient(
            base_url=f"{base_url}/_db/{dbname}", http2=True
        )
        self.jwt = None
        self.jwt_decoded = None

    async def connect(self):
        login_data = {"username": self.username, "password": self.password}
        result = await self.client.post("/_open/auth", json=login_data)
        if result.status_code != 200:
            raise self.DatabaseException(f"Error connecting to Database: {result.text}")
        self.jwt = result.json().get("jwt")
        self.jwt_decoded = jwt.decode(self.jwt, options={"verify_signature": False})

        result = await self.get("/_api/database/current")
        if result.status_code != httpx.codes.OK:
            raise self.DatabaseException("Database not accessible.")

    async def initialize(self):
        await self.connect()
        for k, v in self.managers.items():
            await v.initialize()
        await self.resume_sessions()

    async def run(self):
        while True:
            if not self.jwt_decoded:
                await asyncio.sleep(10)
                continue
            exp = self.jwt_decoded.get("exp")
            current = time.time()
            remaining = exp - current - 120

            if remaining > 0:
                await asyncio.sleep(remaining)
            await self.connect()

    async def request(self, method, url, **kwargs):
        """
        Perform an authenticated request using the stored JWT.

        :param method: HTTP method (e.g., 'get', 'post', 'put', 'delete')
        :param url: URL for the request
        :param kwargs: Additional arguments to pass to httpx request
        """
        if not self.jwt:
            raise self.DatabaseException(
                "JWT is not available. Please authenticate first."
            )

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.jwt}"
        return await getattr(self.dbclient, method)(url, **kwargs, headers=headers)

    async def get(self, url, **kwargs):
        return await self.request("get", url, **kwargs)

    async def post(self, url, **kwargs):
        return await self.request("post", url, **kwargs)

    async def put(self, url, **kwargs):
        return await self.request("put", url, **kwargs)

    async def delete(self, url, **kwargs):
        return await self.request("delete", url, **kwargs)

    async def patch(self, url, **kwargs):
        return await self.request("patch", url, **kwargs)

    async def getProxy(self, data):
        if not (proxy_name := data.get("proxy", None)):
            raise self.DatabaseException(
                f"Document {id} requested with proxy mode, but has no proxy set."
            )
        if not (proxy_class := origin.AUTOPROXY.get(proxy_name, None)):
            raise self.DatabaseException(
                f"Document {id} requested non-existent autoproxy {proxy_name}"
            )
        return proxy_class(data, self)

    async def getDocument(self, id: str, proxy=True):
        result = await self.get(f"/_api/document/{id}")
        if result.status_code != 200:
            raise self.DatabaseException(
                f"Cannot retrieve Document ID '{id}': {result.text}"
            )
        data = result.json()
        if not proxy:
            return data
        return await self.getProxy(data)

    async def query(self, query: str, **kwargs):
        query_data = dict()
        query_data["query"] = query
        if kwargs:
            query_data["bindVars"] = kwargs
        result = await self.post("/_api/cursor", json=query_data)
        if result.status_code != 201:
            raise self.DatabaseException(f"Bad Query: {result.text}")
        cursor = Cursor(result.json(), self)
        async for doc in cursor.results():
            yield doc
        await cursor.close()

    async def query_proxy(self, query: str, **kwargs):
        async for doc in self.query(query, **kwargs):
            yield await self.getProxy(doc)

    async def create_session(self, sid, environ):
        sess_manager = self.managers["session"]
        sess = await sess_manager.create_document(data=dict(), key=sid)
        origin.CONNECTIONS[sid] = sess

    async def resume_sessions(self):
        sess_manager = self.managers["session"]
        async for sess in sess_manager.all_proxy():
            origin.CONNECTIONS[sess.sid] = sess


class CollectionManager:
    name = None
    edge = False
    proxy = None

    async def create_collection(self):
        results = await self.get(f"/_api/collection/{self.name}")
        if results.status_code == 404:
            schema = {"name": self.name}
            if self.edge:
                schema["type"] = 3
            results = await self.post("/_api/collection", json=schema)
            if results.status_code != 200:
                raise self.dbmanager.DatabaseException(
                    f"Could not create collection {self.name}"
                )

    async def create_supplemental(self):
        pass

    async def initialize(self):
        await self.create_collection()
        await self.create_supplemental()

    def __init__(self, dbmanager: DatabaseManager):
        self.dbmanager = dbmanager

    @property
    def request(self):
        return self.dbmanager.request

    @property
    def get(self):
        return self.dbmanager.get

    @property
    def post(self):
        return self.dbmanager.post

    @property
    def put(self):
        return self.dbmanager.put

    @property
    def delete(self):
        return self.dbmanager.delete

    @property
    def patch(self):
        return self.dbmanager.patch

    async def all(self):
        async for doc in self.dbmanager.query(f"FOR doc IN {self.name} RETURN doc"):
            yield doc

    async def all_proxy(self):
        async for doc in self.dbmanager.query_proxy(
            f"FOR doc IN {self.name} RETURN doc"
        ):
            yield doc

    async def create_document(self, data: dict, key=None):
        if key is not None:
            data["_key"] = str(key)
        if self.proxy:
            data["proxy"] = self.proxy
        params = {"returnNew": "true"}
        result = await self.post(
            f"/_api/document/{self.name}", json=data, params=params
        )
        if result.status_code not in (201, 202):
            raise ValueError(f"Could not create {self.name}: {result.text}")
        new_doc = result.json().get("new")
        return (await self.dbmanager.getProxy(new_doc)) if self.proxy else new_doc

    async def count(self) -> int:
        result = await self.get(f"/_api/collection/{self.name}/count")
        if result.status_code == 200:
            return result.json().get("count", 0)
        return 0


class DocumentProxy:
    def __init__(self, data, dbmanager: DatabaseManager):
        self.id = data.get("_id")
        self.dbmanager = dbmanager

    def __str__(self):
        return self.id

    def __repr__(self):
        return f"<{self.__class__.__name__} ({self.id})>"

    async def getDocument(self):
        return await self.dbmanager.getDocument(self.id, proxy=False)

    async def patchDocument(self, data: dict, **kwargs):
        await self.dbmanager.patch(f"/_api/document/{self.id}", json=data, **kwargs)

    async def putDocument(self, data, **kwargs):
        await self.dbmanager.put(f"/_api/document/{self.id}", json=data, **kwargs)

    async def deleteDocument(self):
        await self.dbmanager.delete(f"/_api/document/{self.id}")
