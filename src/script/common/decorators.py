from src.script.input.validation import InputValidator


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

def entity_input(class_method):
    """
    Decorator that wraps input generation methods to handle entity parameter.
    
    Allows the method to be called either with an entity (instance-specific)
    or without (class-level for CLI parsing).
    """
    def wrapper(entity=None, entity_type=None, handler_registry=None, validator=None):
        if entity is not None:
            # Instance-specific call - use entity's properties
            return class_method(
                entity_type=entity.type,
                handler_registry=entity.handler_registry,
                validator=InputValidator(registry=entity.registry, entity=entity),
                entity=entity
            )
        else:
            # Class-level call - use provided parameters
            return class_method(
                entity_type=entity_type,
                handler_registry=handler_registry,
                validator=validator,
                entity=None
            )
    return wrapper