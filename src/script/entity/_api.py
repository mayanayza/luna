import sys
from abc import abstractmethod
from typing import Dict, List

from src.script.constants import EntityType
from src.script.entity._base import EntityBase, ModuleEntity


class Api(ModuleEntity):
    def __init__(self, registry, name: str):
        super().__init__(registry, name)

    @abstractmethod
    def start(self):
        """
        Start the API with the provided application context.
        
        Args:
            app_context: The application context containing registries and other resources
        """
        pass

    def _get_param_values_for_entity_type(self, registry_name: str) -> Dict:
        return {
            'singular': registry_name,
            'plural': f"{registry_name}s",
            'all': 'all'
        }

    def _get_entities_from_params(self, params: Dict[str, str], registry_name: str) -> List[EntityBase]:
        
        registry = self.registry.manager.get_by_name(registry_name)
        param_vals = self._get_param_values_for_entity_type(registry_name)

        for arg_string in param_vals.values():
            if arg_string in params and params[arg_string]:

                    if arg_string == param_vals['singular']:
                        return [ registry.get_by_name( params[param_vals['singular']] ) ]
                    elif arg_string == param_vals['plural']:
                        return [ registry.get_by_name(entity_name) for entity_name in params[param_vals['plural']] ]
                    elif arg_string == param_vals['all']:
                        return registry.get_all_entities()

        return []        

    def dispatch_command(self, registry_name, command, params):
        """
        Dispatch a command to the appropriate registry.
        
        Args:
            registry_name: The name of the registry to target ('project', 'integration', or 'project_integration')
            command: The command to execute
            args: The parsed command line arguments
            app_context: The application context containing registries
            
        Returns:
            The result of the command execution
        """
        try:
            # Get registry manager from app context
                
            registry = self.registry.manager.get_by_name(registry_name)
            if not registry:
                self.logger.error(f"Registry not found: {registry_name}")
                return None

            # Resolve entities from names in command and delete extraneous args from parameter

            entity_types = [EntityType.INTEGRATION, EntityType.PROJECT]

            for entity_type in entity_types:
                
                entities = self._get_entities_from_params(params, entity_type)

                for arg_string in self._get_param_values_for_entity_type(entity_type).values():
                    params.pop(arg_string, None)

                if entities:
                    params[entity_type] = entities if entity_type == registry_name else entities[0]

            target_entities = params[registry_name] if registry_name in params else None
                        
            # Handle registry-level commands vs entity-level commands

            if command in ['list', 'create', 'clear']:
                self.logger.debug(f"Dispatching command '{command}' to {registry_name} with params {params}")
                return registry.invoke_registry_handler(command, params)
            else:
                if target_entities:
                    del params[registry_name]
                    self.logger.debug(f"Dispatching command '{command}' to {registry_name} targeting entities: {str(target_entities)} and params {params}")
                    result = []
                    for entity in target_entities:
                        result.append( registry.invoke_entity_handler(entity, command, params) )
                    return result

                else:
                    self.logger.warning(f"No targets specified for command {command}")
                
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
            
        return None