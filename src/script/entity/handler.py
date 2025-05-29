from typing import Any

from src.script.common.constants import CommandType, EntityType, HandlerType
from src.script.common.decorators import classproperty
from src.script.entity._entity import Entity


class Handler(Entity):
    def __init__(self, 
                 registry, 
                 input_method, 
                 handler_method, 
                 handler_type: HandlerType, 
                 entity_type: EntityType, 
                 entity_registry, 
                 command_type: CommandType, 
                 needs_target, 
                 **kwargs):
        super().__init__(registry, **kwargs)

        self._entity_type = entity_type
        self._entity_registry = entity_registry
        self._command_type = command_type
        self._handler_method = handler_method
        self._input_method = input_method
        self._handler_type = handler_type
        self._needs_target = needs_target

    def __str__(self):
        return f"Handler, entity type '{self.entity_type.value}' command type '{self.command_type.value}'>"

    def __call__(self, *args, **kwargs) -> Any:
        """Make handler callable"""
        try:
            return self.handler(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Handler {self.name} failed: {e}")
            raise

    @property
    def name(self):
        return f"{self._entity_type}-{self._command_type}-{self._handler_type}-{self.uuid}"
    
    @classproperty
    def type(self):
        return EntityType.HANDLER

    @property
    def handler_type(self):
        return self._handler_type
    
    @property
    def entity_type(self):
        return self._entity_type

    @property
    def needs_target(self):
        return self._needs_target
    
    
    @property
    def command_type(self):
        return self._command_type

    @property
    def entity_registry(self):
        return self._entity_registry
    
    @property
    def current_entity(self):
        return self._current_entity

    @current_entity.setter
    def current_entity(self, val):
        self._current_entity = val
    
            
    @property
    def input_obj(self):
        input_obj = self._input_method(
            registry=self.entity_registry,
            handler_registry=self.registry,
        )
        input_obj.add_handler(self.ref)
        return input_obj
    
    def set_current_entity(self, entity):
        """Set the current entity for input generation"""
        self._current_entity = entity

    @property
    def handler(self):
        return self._handler_method