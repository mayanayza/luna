import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, TypeVar, Union

from src.script.entity._base import EntityBase, EntityRef
from src.script.registry._base import Registry
from src.script.registry._manager import RegistryManager

# Define TypeVars for Generic Type Hints
E = TypeVar('E', bound='EntityBase')

@dataclass
class CommandContext:
    """Context for command execution with all necessary parameters."""
    command: str
    # Targets of the command by registry id
    targets: Dict[str, List[EntityRef]] = field(default_factory=dict)
    # Additional parameters for the command
    params: Dict[str, Any] = field(default_factory=dict)
    # The registry that initiated the command
    source_registry_id: Optional[str] = None
    # Registries that have been visited during command execution (to prevent cycles)
    visited_registries: Set[str] = field(default_factory=set)

class CommandDispatcher:
    """Central dispatcher for commands that routes them to appropriate registries."""
    def __init__(self, registry_manager: RegistryManager):
        self.registry_manager = registry_manager
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
    
    def dispatch(self, context: CommandContext) -> Dict[str, List[Any]]:
        """Dispatch a command to all targeted registries and entities."""
        results = {}
        
        # Mark source registry as visited
        if context.source_registry_id:
            context.visited_registries.add(context.source_registry_id)
        
        # Process targets by registry
        for registry_id, entity_refs in context.targets.items():
            # Skip already visited registries
            if registry_id in context.visited_registries:
                continue
            
            context.visited_registries.add(registry_id)
            registry = self.registry_manager.get_registry(registry_id)
            
            if registry and hasattr(registry, 'invoke_entity_handler'):
                # Execute command for each entity in the registry
                registry_results = []
                for ref in entity_refs:
                    entity = registry.get_by_id(ref.entity_id)
                    if entity:
                        try:
                            result = registry.invoke_entity_handler(entity, context.command, context.params)
                            registry_results.append(result)
                        except Exception as e:
                            self.logger.error(f"Error executing command '{context.command}' on entity {ref}: {e}")
                    else:
                        self.logger.warning(f"Entity {ref} not found in registry {registry_id}")
                
                results[registry_id] = registry_results
            else:
                self.logger.warning(f"Registry {registry_id} not found or does not support commands")
        
        return results

class CommandableRegistry(Registry):
    """
    A registry that supports command execution with cross-registry capabilities, and can access the database
    """
    
    def __init__(self, registry_id: str, entity_class):
        super().__init__(registry_id, entity_class)
        self.command_dispatcher: Optional[CommandDispatcher] = None
        self._db: Optional[EntityBase] = None
        # self._apis_loaded = False
        # self._apis = {}
    
    # def load_apis(self, api_registry):
    #     """Load APIs from the api registry."""
    #     if not self._apis_loaded:
    #         self._apis = api_registry.get_all()
    #         self._apis_loaded = True
    #         self.logger.debug(f"Loaded APIs for {self.registry_id} registry")
    
    def set_command_dispatcher(self, dispatcher: CommandDispatcher) -> None:
        """Set the command dispatcher for this registry."""
        self.command_dispatcher = dispatcher

    def dispatch_registry_command(self, command: str, **params) -> Any:
        """
        Dispatch a command that targets this registry itself, not entities within it.
        
        This is a convenience method for commands that don't operate on specific entities
        """
        return self.invoke_registry_handler(command, params)

    def dispatch_entity_command(self, 
                   command: str,
                   targets: Optional[Dict[str, Union[List[str], bool]]] = None,
                   **params) -> Dict[str, List[Any]]:
        """
        Execute a command on targets across registries.
        
        Args:
            command: The command to execute
            targets: Dict mapping registry_ids to either:
                    - List of entity names
                    - Boolean (True to target all entities in that registry)
            **params: Command parameters
        """
        if not self.command_dispatcher:
            self.logger.warning("Command dispatcher not set")
            return {}
        
        resolved_targets = {}
        
        # Handle this registry's targets if not specified
        if not targets:
            targets = {self.registry_id: []}
        
        # Resolve all targets
        for registry_id, target_spec in targets.items():
            if isinstance(target_spec, bool) and target_spec:
                # Target all entities in the registry
                registry = self.manager.get_registry(registry_id)
                if registry:
                    resolved_targets[registry_id] = [
                        entity.ref for entity in registry.get_all_entities()
                    ]
            elif isinstance(target_spec, list):
                # Target specific entities by name
                registry = self.manager.get_registry(registry_id)
                if registry:
                    refs = []
                    for name in target_spec:
                        entity = registry.get_by_name(name)
                        if entity:
                            refs.append(entity.ref)
                        else:
                            self.logger.warning(f"Entity '{name}' not found in registry {registry_id}")
                    if refs:
                        resolved_targets[registry_id] = refs
            else:
                self.logger.warning(f"Invalid target specification for registry {registry_id}")
        
        # Create context and dispatch
        context = CommandContext(
            command=command,
            targets=resolved_targets,
            params=params,
            source_registry_id=self.registry_id
        )
        
        return self.command_dispatcher.dispatch(context)

    def invoke_entity_handler(self, entity, command: str, params: dict) -> Any:
        """
        Execute a command on an entity using reflection to find the handler method.
        
        The handler method should be named using the pattern: handle_{command}
        """
        handler_name = f"handle_{command}"
        
        if hasattr(entity, handler_name):
            handler = getattr(entity, handler_name)
            if callable(handler):
                try:
                    result = handler(**params)
                    self.logger.debug(f"Executed command '{command}' on entity {getattr(entity, 'name', entity.id)}")
                    return result
                except Exception as e:
                    self.logger.error(f"Error executing command '{command}' on entity {getattr(entity, 'name', entity.id)}: {e}")
                    raise
        
        self.logger.warning(f"No handler found for command '{command}' on entity {getattr(entity, 'name', entity.id)}")
        return None

    def invoke_registry_handler(self, command: str, params: dict) -> Any:
        """Execute a command at the registry level using reflection."""
        handler_name = f"handle_{command}"
        
        if hasattr(self, handler_name):
            handler = getattr(self, handler_name)
            if callable(handler):
                try:
                    result = handler(**params)
                    self.logger.debug(f"Executed registry command '{command}'")
                    return result
                except Exception as e:
                    self.logger.error(f"Error executing registry command '{command}': {e}")
                    raise
        
        self.logger.warning(f"No handler found for registry command '{command}'")
        return None
