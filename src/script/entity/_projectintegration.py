from datetime import datetime
from typing import TYPE_CHECKING

from src.script.entity._base import EntityBase, EntityRef, StorableEntity
from src.script.registry._base import Registry

if TYPE_CHECKING:
    pass

class ProjectIntegration(StorableEntity, EntityBase):
    """
    Represents the interface between a project and an integration.
    
    This class creates a bridge between Project and Integration instances, 
    automatically detecting and binding methods and properties that require
    a Project parameter.
    """
    
    def __init__(self, registry: Registry):
        self._project_ref = None
        self._integration_ref = None

        super().__init__(registry)

    @property
    def db_additional_fields(self):
        return {
            'project_id': self._project_ref.entity_id,
            'integration_id': self._integration_ref.entity_id
        }

    def create(self, project_ref: EntityRef, integration_ref: EntityRef):
        try:
            """Create a project integration."""
            self._project_ref = project_ref
            self._integration_ref = integration_ref

            integration = self.registry.manager.get_entity(integration_ref)
            project = self.registry.manager.get_entity(project_ref)

            self.name = f"{project.name} - {integration.name}"

            commands = [method.replace('handler_','') for method in dir(integration) if callable(getattr(integration, method)) and method.startswith("handle_")]
            
            # Set default commands data
            self._data['commands'] = {}
            for command in commands:
                self._data['commands'][command] = {"last_run": False}
            
            # Apply any project_fields from integration config
            self._data['fields'] = {}
            project_fields = getattr(integration, 'config').get('project_fields')
            for field, default_value in project_fields.items():
                self._data['fields'][field] = default_value
                    
            # Bind methods and properties
            # self._bind_members()
            
            return self
        except Exception as e:
            if integration and project:
                self.logger.error(f"Error adding integration {integration.name} to project {project.name}: {e}")
            else:
                self.logger.error(f"Error creating ProjectIntegration: {e}")

    def load(self, project_id, integration_id, **kwargs):
        try:
            integration_registry = self.registry.manager.get_registry('integration')
            project_registry = self.registry.manager.get_registry('project')

            self._integration_ref = integration_registry.get_by_id(integration_id)
            self._project_ref = project_registry.get_by_id(project_id)
            
            super().load(**kwargs)
        except Exception as e:
            self.logger.error(f"Error loading ProjectIntegration: {e}")

    def remove(self):
        try:
            integration = self.registry.manager.get_entity(self._integration_ref)
            project = self.registry.manager.get_entity(self._project_ref)
            integration.remove(project)

            self.registry.unregister_entity(self)

        except Exception as e:
            if integration and project:
                self.logger.error(f"Error removing integration {integration.name} from project {project.name}: {e}")
            else:
                self.logger.error(f"Error removing ProjectIntegration: {e}")

    def setup(self):
        try:
            integration = self.registry.manager.get_entity(self._integration_ref)
            project = self.registry.manager.get_entity(self._project_ref)
            integration.setup(project)
        except Exception as e:
            if integration and project:
                self.logger.error(f"Error setting up integration {integration.name} for project {project.name}: {e}")
            else:
                self.logger.error(f"Error setting up ProjectIntegration: {e}")

    def rename(self):
        try:
            integration = self.registry.manager.get_entity(self._integration_ref)
            project = self.registry.manager.get_entity(self._project_ref)
            integration.rename(project)
        except Exception as e:
            if integration and project:
                self.logger.error(f"Error renaming integration {integration.name} for project {project.name}: {e}")
            else:
                self.logger.error(f"Error renaming ProjectIntegration: {e}")

    def last_run(self, command):
        """Get the last run datetime for a specific command."""
        commands_data = self.data.get('commands', {})
        command_data = commands_data.get(command, {})
        last_run_str = command_data.get('last_run')
        
        if last_run_str and last_run_str is not False:
            try:
                return datetime.strptime(last_run_str, '%d-%b-%Y-%H:%M:%S')
            except (ValueError, TypeError):
                pass
        return None

    def update_last_run(self, command):
        """Update the last run time for a command."""
        # Get current data
        data = self._data
        
        # Ensure commands dict exists
        if 'commands' not in data:
            data['commands'] = {}
            
        # Ensure command entry exists
        if command not in data['commands']:
            data['commands'][command] = {}
            
        # Update last run time
        data['commands'][command]['last_run'] = datetime.now().strftime('%d-%b-%Y-%H:%M:%S')
        
        # Save back to db
        with self.db.transaction():
            self.db.upsert('project_integration', self)

    # def _bind_members(self) -> None:
    #     """
    #     Automatically detect and bind integration methods and properties to this 
    #     ProjectIntegration instance. For members that have a Project parameter,
    #     create wrappers that automatically pass the project.
    #     """
    #     # Bind methods that require project
    #     for method_name, method in self._get_project_aware_methods().items():
    #         wrapped_method = self._create_method_wrapper(method)
    #         setattr(self, method_name, wrapped_method)
        
    #     # Bind properties that require project
    #     for prop_name, prop_dict in self._get_project_aware_properties().items():
    #         descriptor = self._create_property_descriptor(prop_name, prop_dict)
    #         # Add the property to the class
    #         setattr(type(self), prop_name, descriptor)
    
    # def _has_project_parameter(self, func: Callable) -> Tuple[bool, Optional[str]]:
    #     """
    #     Check if a function has a parameter with 'Project' type annotation.
    #     Returns a tuple of (has_project_param, param_name).
    #     """
    #     # Get the function's signature to examine parameters
    #     sig = inspect.signature(func)
        
    #     # Check parameter names - look for 'project' or parameters with 'Project' in annotation
    #     for param_name, param in list(sig.parameters.items())[1:]:  # Skip 'self'
    #         # Check if parameter name is 'project'
    #         if param_name == 'project':
    #             return True, param_name
            
    #         # Check if parameter annotation contains 'Project'
    #         param_annotation = param.annotation
    #         if param_annotation != inspect.Parameter.empty:
    #             if 'Project' in str(param_annotation):
    #                 return True, param_name
                
    #         # Check for 'project_ref' parameter which might be used for EntityRef
    #         if param_name == 'project_ref':
    #             return True, param_name
        
    #     # No project parameter found
    #     return False, None
    
    # def _get_project_aware_methods(self) -> Dict[str, Callable]:
    #     """
    #     Automatically detect methods that have a Project parameter.
    #     """
    #     methods = {}
        
    #     # Get all attributes of the integration
    #     for attr_name in dir(self._integration):
    #         # Skip private methods and properties
    #         if attr_name.startswith('_'):
    #             continue
                
    #         # Skip if it's a property
    #         if isinstance(getattr(type(self._integration), attr_name, None), property):
    #             continue
            
    #         # Get the attribute
    #         attr = getattr(self._integration, attr_name)
            
    #         # Check if it's a callable (method)
    #         if callable(attr):
    #             # Check if it has a Project parameter
    #             has_project, _ = self._has_project_parameter(attr)
    #             if has_project:
    #                 methods[attr_name] = attr
                
    #     return methods
    
    # def _get_project_aware_properties(self) -> Dict[str, Dict[str, Any]]:
    #     """
    #     Automatically detect properties that have getters with a Project parameter.
    #     """
    #     properties = {}
    #     integration_class = type(self._integration)
        
    #     for attr_name in dir(integration_class):
                
    #         attr = getattr(integration_class, attr_name, None)
    #         if not isinstance(attr, property):
    #             continue
                
    #         # Check if the property getter has a Project parameter
    #         getter = attr.fget
    #         if getter:
    #             has_project, _ = self._has_project_parameter(getter)
                
    #             if has_project:
    #                 # Check if setter/deleter also have Project parameters
    #                 setter_has_project = False
    #                 deleter_has_project = False
                    
    #                 if attr.fset:
    #                     setter_has_project, _ = self._has_project_parameter(attr.fset)
                        
    #                 if attr.fdel:
    #                     deleter_has_project, _ = self._has_project_parameter(attr.fdel)
                    
    #                 properties[attr_name] = {
    #                     'property': attr,
    #                     'getter': getter,
    #                     'getter_needs_project': has_project,
    #                     'setter': attr.fset,
    #                     'setter_needs_project': setter_has_project,
    #                     'deleter': attr.fdel,
    #                     'deleter_needs_project': deleter_has_project
    #                 }
                
    #     return properties
    
    # def _create_method_wrapper(self, method: Callable) -> Callable:
    #     """
    #     Create a wrapper that injects the project parameter for methods.
    #     """
    #     # Find the Project parameter
    #     has_project, project_param_name = self._has_project_parameter(method)
    #     if not has_project or not project_param_name:
    #         # Fallback to 'project' if not found but should have a project param
    #         project_param_name = 'project'
        
    #     def wrapper(*args, **kwargs):
    #         # If the parameter is project_ref, pass the project's ref
    #         if project_param_name == 'project_ref':
    #             if project_param_name not in kwargs:
    #                 kwargs[project_param_name] = self._project.ref
    #         # Otherwise pass the project instance
    #         elif project_param_name not in kwargs:
    #             kwargs[project_param_name] = self._project
            
    #         # Pass instance_id if the method supports it
    #         sig = inspect.signature(method)
    #         if 'instance_id' in sig.parameters and 'instance_id' not in kwargs:
    #             kwargs['instance_id'] = self._instance_id
                
    #         # Call the original method
    #         return method(self._integration, *args, **kwargs)
            
    #     # Copy metadata from original method
    #     wrapper.__name__ = method.__name__
    #     wrapper.__doc__ = method.__doc__
        
    #     return wrapper
    
    # def _create_property_descriptor(self, prop_name: str, prop_dict: Dict[str, Any]):
    #     """
    #     Create a property descriptor that handles project injection for properties.
    #     """
    #     # Extract property components
    #     getter = prop_dict['getter']
    #     setter = prop_dict['setter']
    #     deleter = prop_dict['deleter']
        
    #     # Get the Project parameter names
    #     has_project, getter_project_param = self._has_project_parameter(getter)
    #     if not has_project or not getter_project_param:
    #         getter_project_param = 'project'
            
    #     # Create descriptor methods
    #     def get_value(instance):
    #         if instance is None:
    #             return None
            
    #         try:
    #             # Prepare kwargs
    #             kwargs = {}
                
    #             # Handle project_ref parameter
    #             if getter_project_param == 'project_ref':
    #                 kwargs[getter_project_param] = instance._project.ref
    #             else:
    #                 # Call getter with project parameter
    #                 kwargs[getter_project_param] = instance._project
                
    #             # Add instance_id if supported
    #             sig = inspect.signature(getter)
    #             if 'instance_id' in sig.parameters:
    #                 kwargs['instance_id'] = instance._instance_id
                    
    #             return getter(instance._integration, **kwargs)
    #         except Exception as e:
    #             instance.logger.error(f"Error in property getter for {prop_name}: {e}")
    #             return None
                
    #     def set_value(instance, value):
    #         if setter is None:
    #             raise AttributeError(f"can't set attribute '{prop_name}'")
            
    #         try:    
    #             # Check if setter needs project
    #             has_project, param_name = self._has_project_parameter(setter)
                
    #             # Prepare kwargs
    #             kwargs = {}
                
    #             if has_project and param_name:
    #                 if param_name == 'project_ref':
    #                     kwargs[param_name] = instance._project.ref
    #                 else:
    #                     kwargs[param_name] = instance._project
                
    #             # Add instance_id if supported
    #             sig = inspect.signature(setter)
    #             if 'instance_id' in sig.parameters:
    #                 kwargs['instance_id'] = instance._instance_id
                
    #             setter(instance._integration, value, **kwargs)
    #         except Exception as e:
    #             instance.logger.error(f"Error in property setter for {prop_name}: {e}")
                    
    #     def del_value(instance):
    #         if deleter is None:
    #             raise AttributeError(f"can't delete attribute '{prop_name}'")
                
    #         try:
    #             # Check if deleter needs project
    #             has_project, param_name = self._has_project_parameter(deleter)
                
    #             # Prepare kwargs
    #             kwargs = {}
                
    #             if has_project and param_name:
    #                 if param_name == 'project_ref':
    #                     kwargs[param_name] = instance._project.ref
    #                 else:
    #                     kwargs[param_name] = instance._project
                
    #             # Add instance_id if supported
    #             sig = inspect.signature(deleter)
    #             if 'instance_id' in sig.parameters:
    #                 kwargs['instance_id'] = instance._instance_id
                
    #             deleter(instance._integration, **kwargs)
    #         except Exception as e:
    #             instance.logger.error(f"Error in property deleter for {prop_name}: {e}")
        
    #     # Create and return the property
    #     return property(
    #         get_value,
    #         set_value if setter else None,
    #         del_value if deleter else None,
    #         doc=getattr(prop_dict['property'], '__doc__', f"Property {prop_name}")
    #     )