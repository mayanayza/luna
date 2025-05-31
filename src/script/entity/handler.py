from typing import Any

from src.script.common.decorators import classproperty
from src.script.common.enums import CommandType, EntityQuantity, EntityType, HandlerType
from src.script.entity._entity import Entity
from src.script.input.input import Input, InputField, InputGroup


class Handler(Entity):
    def __init__(self, 
                 registry, 
                 input_method, 
                 handler_method, 
                 handler_type: HandlerType, 
                 entity_type: EntityType, 
                 entity_registry, 
                 command_type: CommandType, 
                 source_class,
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
        self._source_class = source_class

        self._name = f"{self._entity_type.value}-{self._command_type.value}-{self._handler_type.value}-{self.uuid}"

    def __str__(self):
        return self.name

    def __call__(self, *args, **kwargs) -> Any:
        """Make handler callable"""
        try:
            return self.handler(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Handler {self.name} failed: {e}")
            raise
    
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
    def entity_quantity(self):
        """Get entity quantity from the decorated handler method"""
        if hasattr(self._handler_method, '_entity_quantity'):
            return self._handler_method._entity_quantity
        return EntityQuantity.SINGLE  # Default

    def get_entity_param_name(self):
        """Get the parameter name for entities based on quantity"""
        if self.entity_quantity == EntityQuantity.SINGLE:
            return self._entity_type.value
        else:
            return f"{self._entity_type.value}s"

    def get_entity_selector_config(self):
        """Get configuration for entity selector field based on handler requirements"""
        quantity = self.entity_quantity
        
        if quantity == EntityQuantity.SINGLE:
            return {
                'allow_multiple': False,
                'allow_all': False,
                'required': True
            }
        elif quantity == EntityQuantity.MULTIPLE:
            return {
                'allow_multiple': True,
                'allow_all': True,
                'required': True
            }
        elif quantity == EntityQuantity.MULTIPLE_OPTIONAL:
            return {
                'allow_multiple': True,
                'allow_all': True,
                'required': False
            }
    
    @property
    def input_obj(self):
        """Get input object for runtime"""
        return self._call_input_method()

    @property
    def proxy_input_obj(self):
        """Get safe input object for CLI parsing"""
        return self._call_input_method(_proxy_mode=True)

    def _call_input_method(self, **extra_kwargs):
        """Helper to call input method and apply proxy transformations if needed"""
        
        # Extract proxy mode flag
        proxy_mode = extra_kwargs.pop('_proxy_mode', False)
        
        # Get the input object from the method
        input_obj = self._execute_input_method(**extra_kwargs, proxy_mode=proxy_mode)
        
        # Apply proxy transformations if in proxy mode
        if proxy_mode:
            return self._apply_proxy_transformations(input_obj, **extra_kwargs)
        
        return input_obj
    
    def _execute_input_method(self, proxy_mode=False, **extra_kwargs):
        """Execute the input method with appropriate arguments"""
        
        # If in proxy mode, create proxy kwargs
        if proxy_mode:
            extra_kwargs = self._create_proxy_kwargs(**extra_kwargs)
        
        try:
            # Most of our methods are functions that expect cls as first argument
            if isinstance(self._input_method, type(lambda: None)):  # It's a function
                # Call as function with class as first argument
                return self._input_method(
                    self._source_class,  # Pass class as first argument
                    registry=self.entity_registry,
                    handler_registry=self.registry,
                    **extra_kwargs
                )
            
            elif hasattr(self._input_method, '__self__'):
                # It's a bound method - call directly without class argument
                return self._input_method(
                    registry=self.entity_registry,
                    handler_registry=self.registry,
                    **extra_kwargs
                )
            
            else:
                # Fallback - try calling as function with class
                return self._input_method(
                    self._source_class,
                    registry=self.entity_registry,
                    handler_registry=self.registry,
                    **extra_kwargs
                )
        
        except Exception:
            if proxy_mode:
                # If proxy creation fails, return minimal input
                return self._create_minimal_fallback_input(**extra_kwargs)
            raise

    def _apply_proxy_transformations(self, input_obj, **kwargs):
        """Apply proxy transformations to make input structure safe"""
        try:
            return self._proxify_input_structure(input_obj)
        except Exception:
            # If proxy transformation fails, return minimal input
            return self._create_minimal_fallback_input(**kwargs)

    def _create_proxy_kwargs(self, **kwargs):
        """Create proxy entities and safe values for missing kwargs"""
        proxy_kwargs = kwargs.copy()
        
        # The registry INSTANCE should be in kwargs, not args
        registry_instance = self.entity_registry
        
        if registry_instance and hasattr(registry_instance, 'entity_type'):
            try:
                # Now access the property on the actual instance
                entity_type_enum = registry_instance.entity_type
                entity_param = entity_type_enum.value
                
                if entity_param not in proxy_kwargs:
                    proxy_kwargs[entity_param] = EntityProxy(entity_type_enum, registry_instance)
                    
            except Exception as e:
                print(f"Debug error: {e}")
                print(f"Registry instance: {registry_instance}")
                print(f"Registry type: {type(registry_instance)}")
        
        return proxy_kwargs

    def _proxify_input_structure(self, input_obj):
        """Recursively make input structure safe by providing fallbacks"""
        if isinstance(input_obj, InputField):
            return self._proxify_field(input_obj)
        elif isinstance(input_obj, (InputGroup, Input)):
            return self._proxify_group(input_obj)
        else:
            return input_obj

    def _proxify_field(self, field):
        """Create safe version of input field"""
        safe_field = InputField(
            name=field.name,
            title=getattr(field, 'title', field.name.title()),
            field_type=getattr(field, 'field_type', str),
            required=getattr(field, 'required', False),
            description=getattr(field, 'description', None),
            short_name=getattr(field, 'short_name', None),
            param_type=getattr(field, 'param_type', 'named'),
            hidden=getattr(field, 'hidden', False)
        )
        
        # Safe choices handling
        if hasattr(field, 'choices'):
            try:
                if callable(field.choices):
                    safe_field.choices = []  # Fallback for callable choices
                else:
                    safe_field.choices = field.choices
            except:
                safe_field.choices = []
        
        # Safe default value handling
        if hasattr(field, 'default_value'):
            try:
                if callable(field.default_value):
                    safe_field.default_value = self._get_type_fallback(field.field_type)
                else:
                    safe_field.default_value = field.default_value
            except:
                safe_field.default_value = self._get_type_fallback(field.field_type)
        
        return safe_field

    def _proxify_group(self, group):
        """Create safe version of input group"""
        safe_children = []
        
        try:
            if hasattr(group, 'children'):
                for child_name, child_node in group.children.items():
                    try:
                        safe_child = self._proxify_input_structure(child_node)
                        safe_children.append(safe_child)
                    except:
                        continue  # Skip problematic children
        except:
            pass
        
        if isinstance(group, Input):
            return Input(
                name=group.name,
                title=getattr(group, 'title', group.name.title()),
                entity_type=getattr(group, 'entity_type', None),
                command_type=getattr(group, 'command_type', None),
                handler_registry=getattr(group, 'handler_registry', None),
                children=safe_children
            )
        else:
            return InputGroup(
                name=group.name,
                title=getattr(group, 'title', group.name.title()),
                children=safe_children
            )

    def _create_minimal_fallback_input(self, **kwargs):
        """Create minimal input when all else fails"""
        registry_instance = self.entity_registry
        handler_registry = self.registry
        
        if registry_instance:
            try:
                # Access the property on the instance
                entity_type_enum = registry_instance.entity_type
                type_name = entity_type_enum.value
                    
                return Input(
                    name=f"{type_name}_fallback",
                    title=f"Fallback {type_name.title()}",
                    entity_type=entity_type_enum,
                    handler_registry=handler_registry,
                    children=[]
                )
            except Exception as e:
                print(f"Debug fallback error: {e}")
                print(f"Debug: registry_instance: {registry_instance}")
        
        # Ultimate fallback
        return Input(
            name="fallback_input",
            title="Fallback Input",
            handler_registry=handler_registry,
            children=[]
        )

    def _get_type_fallback(self, field_type):
        """Get safe fallback value for field type"""
        type_fallbacks = {
            str: "",
            int: 0,
            float: 0.0,
            bool: False,
            list: [],
            dict: {}
        }
        return type_fallbacks.get(field_type, None)

    def set_current_entity(self, entity):
        """Set the current entity for input generation"""
        self._current_entity = entity

    @property
    def handler(self):
        def wrapped(**kwargs):
            return self._handler_method(
                registry=self.entity_registry,
                handler_registry=self.registry,
                **kwargs
            )
        return wrapped

class EntityProxy:
    """Lightweight entity proxy for safe CLI parsing"""
    
    def __init__(self, entity_type, registry):
        self.type = entity_type
        self.name = f"proxy-{entity_type.value}"
        self.registry = registry
        self._entity_class = registry.entity_class
    
    @property
    def config(self):
        """Return proxy config from class-level definitions"""
        if hasattr(self._entity_class, '_config_fields'):
            return Input(
                name="config_proxy",
                title="Configuration",
                children=self._entity_class._config_fields
            )
        return Input(name="config_proxy", title="Configuration", children=[])
    
    def __getattr__(self, name):
        """Provide safe fallbacks for any attribute access"""
        if hasattr(self._entity_class, name):
            class_attr = getattr(self._entity_class, name)
            if isinstance(class_attr, (list, dict)):
                return type(class_attr)()  # Empty list/dict
            elif isinstance(class_attr, str):
                return f"proxy-{name}"
            else:
                return class_attr
        
        # Smart fallbacks based on name patterns
        if name.endswith('_fields'):
            return []
        elif name.startswith('get_') and name.endswith('_fields'):
            return lambda: []
        elif name.startswith('get_'):
            return lambda *args, **kwargs: []
        else:
            return f"proxy-{name}"