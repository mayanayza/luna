import sys
from abc import abstractmethod
from typing import Dict, List, Optional

from src.script.constants import Command, EntityType
from src.script.entity._base import (
    CreatableEntity,
    EntityBase,
    ModuleEntity,
    StorableEntity,
)


class Api(ModuleEntity):
    def __init__(self, registry, name: str):
        super().__init__(registry, EntityType.API, name)

    @abstractmethod
    def start(self):
        """
        Start the API with the provided application context.
        
        Args:
            app_context: The application context containing registries and other resources
        """
        pass

    @abstractmethod
    def _process_command(self, args):
        pass

    def handle_entity_create(self, args, additional_params: Optional[Dict] = {}):
        # Create and fill the form
        entity_type = self.ui.context.entity_type
        form_data = CreatableEntity.create_form(self.ui, entity_type)
        if not form_data:
            return None
        
        params = {
            'name': form_data["name"],
            'title': self.ui.validator.format_kebabcase_to_titlecase(form_data["name"]),
            'emoji': form_data["emoji"],
            **additional_params
        }

        result = self.dispatch_command(entity_type, Command.CREATE, params)
        
        if result:
            self.ui.respond(f"Created {entity_type} {result.name}", "success")
        else:
            self.ui.respond(f"Failed to create {entity_type}", "error")
        
        return result

    def _select_entity(self):
        entity_type = self.ui.context.entity_type
        entity_name = StorableEntity.select_form(self.ui, entity_type, Command.EDIT)
        if not entity_name:
            return None

        entity = self.ui.context.current_entity_registry.get_by_name(entity_name)
    
        if not entity:
            self.ui.respond(f"{entity_type.title()} '{entity_name}' not found", "error")
            return None
        return entity

    def handle_entity_rename(self, entity: Optional[EntityBase] = None):
        
        entity = self._select_entity() if not entity else entity   

        rename_data = entity.rename_form(self.ui)

        if not rename_data:
            return None

        new_name = rename_data["new_name"]
        new_emoji = rename_data["new_emoji"]
        new_title = self.ui.validator.format_kebabcase_to_titlecase(new_name)

        params = {
            entity.type: entity.name,
            'new_name': new_name,
            'new_title': new_title,
            'new_emoji': new_emoji
        }

        result = self.dispatch_command(entity.type, 'rename', params)

        if result:
            self.ui.respond(f"Updated {entity.type} '{entity.name}'", "success")
            self.ui.respond(f"  Name changed to: {result.name}", "success")
            self.ui.respond(f"  Title changed to: {result.title}", "success")
            self.ui.respond(f"  Emoji changed to: {result.emoji or 'None'}", "success")
        else:
            self.ui.respond(f"Failed to rename {entity.type}", "error")
        
        return result

    def handle_entity_edit(self, entity: Optional[EntityBase] = None):
        """
        Handle entity config editing using form-based approach.
        
        Args:
            args: Command line arguments
            
        Returns:
            Any: Edit result
        """
        entity = self._select_entity() if not entity else entity            
        
        self.ui.respond(f"Editing configuration for '{entity.name}'", "info")
        
        success = self.ui.form_builder.fill_form_interactive(entity.config)
        if success:
            self.ui.respond("Editing completed!", "success")
        else:
            return None

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

                    if len(entities) > 1 and entity_type != registry_name:
                        self.logger.error(f"More than one {entity_type} entity provided for a command to registry {registry_name}. Only one non-target entity should only be provided in a command.")
                        return
                    else:
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