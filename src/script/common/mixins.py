from abc import ABC, abstractmethod


class Interfaceable(ABC):
    pass
    
class Listable(Interfaceable):
    pass

class Storable(Interfaceable):
    pass

class Creatable(Interfaceable):
    pass

class CreatableFromModule(Interfaceable):
    pass

class ClassWithHandlers(ABC):
    """Mixin class that provides automatic handler registration"""
    _handlers_registered = {}  # Track per class
    
    def __init__(self, registry=None, **kwargs):
        # Register handlers for this class AND all parent classes
        self._register_all_handlers()

    def _register_all_handlers(self):
        """Register handlers for this class, but only once per class"""
        class_name = self.__class__.__name__
        
        # Check if handlers for this exact class have already been registered
        if class_name in self._handlers_registered:
            self.logger.debug(f"Handlers for {class_name} already registered, skipping")
            return
        
        if hasattr(self, '_register_handlers_for_class'):
            self.logger.debug(f"Registering handlers for {class_name}")
            self._register_handlers_for_class()
        
            # Mark this class as having registered handlers
            self._handlers_registered[class_name] = True
        else:
            self.logger.debug(f"No handlers to register for {class_name}")

    def _register_handlers_for_class(self):
        """Register handlers for this class and all parent classes that have handlers"""
        # Collect all handler configs from the inheritance chain
        all_handler_configs = {}  # Use dict to track by command_type for deduplication
        
        # Walk through MRO in reverse order (most base class first)
        for cls in reversed(self.__class__.__mro__):
            if hasattr(cls, '_handler_configs') and cls._handler_configs:
                self.logger.debug(f"Found handler configs in {cls.__name__}: {[config['command_type'].value for config in cls._handler_configs]}")
                
                for handler_config in cls._handler_configs:
                    command_type = handler_config['command_type']
                    
                    # Create an enhanced config that includes source class info
                    enhanced_config = handler_config.copy()
                    enhanced_config['_source_class'] = cls
                    enhanced_config['_source_class_name'] = cls.__name__
                    
                    # Track the source class for each command type
                    # Later classes in MRO (more derived) will override earlier ones
                    all_handler_configs[command_type] = enhanced_config
        
        # Now register handlers, ensuring we only register each command_type once
        # with the most derived implementation
        registered_commands = set()
        
        for command_type, handler_config in all_handler_configs.items():
            class_name = handler_config['_source_class_name']
            
            if command_type not in registered_commands:
                self.logger.debug(f"Registering {command_type.value} handler from {class_name}")
                self._register_class_handler(handler_config)
                registered_commands.add(command_type)
            else:
                self.logger.debug(f"Skipping duplicate {command_type.value} handler from {class_name}")

    @abstractmethod
    def _register_class_handler(self, handler_config):
        """
        Register a single handler based on the provided configuration.
        
        The handler_config dict contains:
        - command_type: The CommandType enum value
        - input_method_name: Name of the method that generates inputs
        - handler_method_name: Name of the method that handles the command
        - _source_class: The class where this handler was originally defined
        - _source_class_name: Name of the source class (for logging)
        """
        pass