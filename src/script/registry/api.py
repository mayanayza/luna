

from src.script.common.constants import EntityType
from src.script.entity.api import Api
from src.script.registry._registry import ListableEntityRegistry


class ApiRegistry(ListableEntityRegistry):

    def __init__(self, manager):
        super().__init__(EntityType.API, Api, manager)
        self.loader.load_from_module('src.script.api')        

        