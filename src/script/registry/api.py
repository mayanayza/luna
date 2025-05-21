

from src.script.entity._api import Api
from src.script.registry._base import Registry


class ApiRegistry(Registry):

    def __init__(self):
        super().__init__('api', Api)

    def load(self):
        self.load_from_module('src.script.api')

        