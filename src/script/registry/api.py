

from src.script.common.enums import EntityType
from src.script.entity.api import Api
from src.script.registry._registry import ListableEntityRegistry


class ApiRegistry(ListableEntityRegistry):

    def __init__(self, manager):
        super().__init__(EntityType.API, Api, manager)
        self.module_loader.load('src.script.api')        

        