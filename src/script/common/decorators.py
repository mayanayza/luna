from functools import wraps
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from src.script.entity._enum import EntityQuantity


class classproperty:
    def __init__(self, func):
        self.func = func
    
    def __get__(self, instance, owner):
        return self.func(owner)

def register_handlers(*handler_configs):
    """
    Decorator to automatically register handlers for an entity class.
    
    Usage:
    @register_handlers(
        {
            'handler_method_name': 'handle_delete',
            'command_type': CommandType.DELETE,
            'input_method_name': 'get_delete_inputs'
        },
        {
            'handler_method_name': 'handle_rename', 
            'command_type': CommandType.RENAME,
            'input_method_name': 'get_rename_inputs',
            'needs_target_entities': True  # Optional, defaults to True
        }
    )
    """
    def decorator(cls):
        cls._handler_configs = handler_configs
        return cls
    return decorator

def entity_quantity(quantity: 'EntityQuantity'):
    """
    Decorator to specify entity quantity requirements for handler methods.
    
    Usage:
        @entity_quantity(EntityQuantity.SINGLE)
        @classmethod
        def handle_delete(cls, project, **kwargs):
            ...
            
        @entity_quantity(EntityQuantity.MULTIPLE)
        @classmethod
        def handle_add_integration(cls, projects, **kwargs):
            ...
    """
    def decorator(func: Callable) -> Callable:
        func._entity_quantity = quantity
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        wrapper._entity_quantity = quantity
        return wrapper
    
    return decorator