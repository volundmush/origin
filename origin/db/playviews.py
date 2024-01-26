from .core import DocumentProxy, CollectionManager


class PlayviewManager(CollectionManager):
    name = "playview"
    edge = True


class Playview(DocumentProxy):
    async def join_session(self, session):
        if not self.sessions.all():
            # this is the first session.
            await self.at_init_playview(session)
        self.sessions.add(session)
        if self.sessions.count() == 1:
            await self.at_start_playview(session)

    async def at_init_playview(self, session, **kwargs):
        pass

    async def at_start_playview(self, session, **kwargs):
        await self.at_login(**kwargs)

    async def at_login(self, **kwargs):
        await self.record_login()
        await self.unstow()
        await self.announce_join_game()

    async def record_login(self, current_time=None, **kwargs):
        if current_time is None:
            current_time = utcnow()
        p = self.id.playtime
        p.last_login = current_time
        p.save(update_fields=["last_login"])

        ca = p.per_user.get_or_create(user=self.user)[0]
        ca.last_login = current_time
        ca.save(update_fields=["last_login"])

    async def unstow(self):
        from origin.db.objects.objects import DefaultObject

        if data := await self.id.attributes.get("location", category="_system"):
            zone_dbref, arbitrary_data = data

            if found := DefaultObject.find_dbref(zone_dbref):
                if zone := found.zone:
                    pass

    async def announce_join_game(self):
        pass
