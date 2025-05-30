from typing import Any, Dict

from src.script.api._enum import CommandType
from src.script.common.decorators import (
    classproperty,
    entity_quantity,
    register_handlers,
)
from src.script.entity._entity import CreatableEntity, EntityType
from src.script.entity._enum import EntityQuantity
from src.script.input.factory import InputFactory
from src.script.input.input import Input, InputField
from src.script.registry._base import Registry


@register_handlers(
    {
        'input_method_name': 'get_add_integration_inputs',
        'handler_method_name': 'handle_add_integration',
        'command_type': CommandType.ADD_INTEGRATION,
    },
    {
        'input_method_name': 'get_remove_integration_inputs',
        'handler_method_name': 'handle_remove_integration',
        'command_type': CommandType.REMOVE_INTEGRATION,
    },
)
class Project(CreatableEntity):

    def __init__(self, registry: Registry, **kwargs) -> None:    
        super().__init__(registry, **kwargs)

    @classproperty
    def type(self):
        return EntityType.PROJECT

    @classproperty
    def short_name(self):
        return 'p'  

     ######                                ##
       ##                                  ##
       ##     ## ###   ######   ##   ##  ######    #####
       ##     ###  ##  ##   ##  ##   ##    ##     ##
       ##     ##   ##  ##   ##  ##   ##    ##      ####
       ##     ##   ##  ##   ##  ##  ###    ##         ##
     ######   ##   ##  ######    ### ##     ###   #####
                       ##
    @classmethod
    def get_add_integration_inputs(cls, registry, handler_registry, **kwargs) -> Input:
        
        integration_registry = registry.manager.get_by_entity_type(EntityType.INTEGRATION)

        return Input(
            name="project_add_integration",
            title="Add Integration",
            entity_type=EntityType.PROJECT,
            handler_registry=handler_registry,
            command_type=CommandType.ADD_INTEGRATION,
            children=[
                InputFactory.entity_target_selector_field(integration_registry)
            ]
        )

    @classmethod
    def get_remove_integration_inputs(cls, handler_registry, registry, **kwargs) -> Input:
        
        project_integration_registry = registry.manager.get_by_entity_type(EntityType.PROJECT_INTEGRATION)

        return Input(
            name="project_remove_integration",
            title="Remove Integration",
            entity_type=EntityType.PROJECT,
            handler_registry=handler_registry,
            command_type=CommandType.REMOVE_INTEGRATION,
            children=[
                InputField(
                    name="project_integration",
                    title=f"Select {registry.entity_type.value.title()}",
                    field_type=project_integration_registry.entity_class,
                    required=True,
                    choices=lambda values: [entity for entity in project_integration_registry.get_all_entities() if entity.project_uuid == values.project.uuid],  # Pass the function, not the result
                    prompt=f"Select {registry.entity_type.value}: ",
                    description="Choose project integration to remove"
                )
            ]
        )

     ##   ##                         ##   ###
     ##   ##                         ##    ##
     ##   ##   ######  ## ###    ######    ##      #####   ## ###    #####
     #######  ##   ##  ###  ##  ##   ##    ##     ##   ##  ###      ##
     ##   ##  ##   ##  ##   ##  ##   ##    ##     #######  ##        ####
     ##   ##  ##  ###  ##   ##  ##   ##    ##     ##       ##           ##
     ##   ##   ### ##  ##   ##   ######   ####     #####   ##       #####

    @classmethod
    @entity_quantity(EntityQuantity.SINGLE)
    def handle_rename(cls, project, **kwargs) -> Dict[str, Any]:
        """Rename this project."""
        try:
            old_name, old_emoji, old_title = super().rename(**kwargs)
            
            # Update all integrations
            pi_registry = project.registry.manager.get_by_entity_type(EntityType.PROJECT_INTEGRATION)
            pi_registry.rename_pis_for_project(
                                project_ref=project.ref,
                                new_name=project.name,
                                new_title=project.title,
                                new_emoji=project.emoji,
                                old_name=old_name,
                                old_title=old_title,
                                old_emoji=old_emoji)
            
            # Save changes to DB
            project.db.upsert(EntityType.PROJECT.value, project)
            
            project.logger.info(f"Renamed project from {old_name} to {project.name}")
        except Exception as e:
            project.logger.error(f"Error renaming project: {e}")
            raise

    @classmethod
    @entity_quantity(EntityQuantity.SINGLE)
    def handle_delete(cls, project, **kwargs):
        """Delete this project."""
        try:
            # Remove all project integrations
            pi_registry = project.registry.manager.get_by_entity_type(EntityType.PROJECT_INTEGRATION)
            pi_registry.remove_pis_for_project(project.ref)
            
            # Delete from DB
            with project.db.transaction():
                table = getattr(project.db.dal, EntityType.PROJECT.value)
                project.db.dal(table.id == project.db_id).delete()
            
            # Unregister from registry
            project.registry.unregister_entity(project)
            
            project.logger.info(f"Deleted project {project.name}")
            return True
        except Exception as e:
            project.logger.error(f"Error deleting project: {e}")
            raise
     
        return None

    @classmethod
    @entity_quantity(EntityQuantity.MULTIPLE)
    def handle_add_integration(cls, projects, integration, **kwargs):

        pi_registry = projects[0].registry.manager.get_by_entity_type(EntityType.PROJECT_INTEGRATION)

        for project in projects:
            pi = pi_registry.add_pi(project.ref, integration.ref)
            pi.setup()
            
            project.logger.info(f"Added integration '{pi.name}' to project {project.name}")
        
        return pi

    @classmethod
    @entity_quantity(EntityQuantity.SINGLE)
    def handle_remove_integration(cls, project, project_integration, **kwargs):            
        pi_registry = project.registry.manager.get_by_entity_type(EntityType.PROJECT_INTEGRATION)
        project_integration = project_integration

        removed_name = pi_registry.remove_pi(project_integration)

        project.logger.info(f"Removed integration '{removed_name}' from project {project.name}")


            # if self.data == {}:
        #     self.data = {
        #         'metadata': {
        #             'primary_url_integration': 'website',
        #             'status': 'backlog',
        #             'priority': 0,
        #             'tagline': '',
        #             'notes': '',
        #             'tags': []
        #         },
        #         'media': {
        #             'embeds': [],
        #             'featured': {
        #                 'type': 'image',
        #                 'source': '',
        #                 'language': '',
        #                 'start_line': 0,
        #                 'end_line': 0
        #             }
        #         },
        #         'attributes': {
        #             'physical': {
        #                 'dimensions': {
        #                     'width': '',
        #                     'height': '',
        #                     'depth': '',
        #                     'unit': ''
        #                 },
        #                 'weight': {
        #                     'value': '',
        #                     'unit': ''
        #                 },
        #                 'materials': []
        #             },
        #             'technical_requirements': {
        #                 'power': '',
        #                 'space': '',
        #                 'lighting': '',
        #                 'mounting': '',
        #                 'temperature_range': '',
        #                 'humidity_range': '',
        #                 'ventilation_needs': ''
        #             },
        #             'exhibition': {
        #                 'setup': {
        #                     'time_required': '',
        #                     'people_required': '',
        #                     'tools_required': [],
        #                     'instructions': []
        #                 },
        #                 'maintenance': {
        #                     'tasks': [],
        #                     'supplies_needed': []
        #                 },
        #                 'history': []
        #             }
        #         }
        #     }