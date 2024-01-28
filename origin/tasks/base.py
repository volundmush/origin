class TaskRunner:
    def __call__(self, core, delta_time: float):
        return self.run(core, delta_time)

    async def run(self, core, delta_time: float):
        pass
