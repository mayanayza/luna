from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


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