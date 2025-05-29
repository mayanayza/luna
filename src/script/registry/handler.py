

from src.script.common.constants import EntityType
from src.script.entity.handler import Handler
from src.script.registry._base import Registry


class HandlerRegistry(Registry):

    def __init__(self, manager):
        super().__init__(EntityType.HANDLER, Handler, manager)

    def register_entity(self, handler: Handler) -> None:
        """Register a handler, replacing any existing handler with same entity_type and command_type."""
        
        # Check if a handler with the same entity_type and command_type already exists
        existing_handler = self.get_handler_by_entity_and_command_types(
            handler.entity_type, 
            handler.command_type
        )
        
        if existing_handler:
            # Unregister the existing handler
            self.logger.warning(f"Replacing existing handler: {existing_handler}")
            self.unregister_entity(existing_handler)
        
        # Register the new handler using the parent class method
        super().register_entity(handler)

    def get_handler_by_entity_and_command_types(self, entity_type, command_type):
        for handler in self.get_all_entities():
            if handler.entity_type is entity_type and handler.command_type is command_type:
                return handler
        return None