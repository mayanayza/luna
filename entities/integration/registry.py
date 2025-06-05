from registries.base import Registry


class IntegrationRegistryBase(Registry):

    def __init__(self, manager):
        super().__init__(manager)