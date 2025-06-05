from registries.base import Registry


class ProjectRegistryBase(Registry):

    def __init__(self, manager):
        super().__init__(manager)