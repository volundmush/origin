class AttributeHandler:
    def __init__(self, obj):
        self.obj = obj

    async def get(self, key: str, default=None, category: str = ""):
        if found := self.obj.attr_data.filter(category=category, name=key).first():
            return found.value
        return default

    async def add(self, key: str, value, category: str = ""):
        if found := self.obj.attr_data.filter(category=category, name=key).first():
            found.value = value
            found.save(update_fields=["value"])
        else:
            self.obj.attr_data.create(category=category, name=key, value=value)

    async def remove(self, key: str, category: str = ""):
        if found := self.obj.attr_data.filter(category=category, name=key).first():
            found.delete()

    async def clear(self, category=""):
        self.obj.attr_data.filter(category=category).delete()

    async def all(self, category: str = ""):
        out = dict()
        for attr in self.obj.attr_data.filter(category=category):
            out[attr.name] = attr.value
        return out
