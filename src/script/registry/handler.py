

from src.script.entity._handler import Handler
from src.script.registry._base import CommandableRegistry


class HandlerRegistry(CommandableRegistry):

    def __init__(self):
        super().__init__('handler', Handler)

    def load(self):
        pass