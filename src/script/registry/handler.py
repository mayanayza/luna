

from typing import List

from src.script.common.enums import CommandType, EntityType, HandlerType
from src.script.entity.handler import Handler
from src.script.registry._base import Registry


class HandlerRegistry(Registry):

    def __init__(self, manager):
        super().__init__(EntityType.HANDLER, Handler, manager)

    def get_system_handler_for_entity_and_command_type(self, entity_type: EntityType, command_type: CommandType):
        return next(filter(
            lambda h: h.handler_type == HandlerType.SYSTEM, 
            self.get_handlers_by_entity_and_command_types(entity_type, command_type)
        ))

    def get_handlers_by_entity_and_command_types(self, entity_type: EntityType, command_type: CommandType) -> List[Handler]:
        return [handler for handler in self.get_all_entities() if handler.entity_type is entity_type and handler.command_type is command_type]