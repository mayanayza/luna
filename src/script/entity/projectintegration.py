
from src.script.common.decorators import (
    classproperty,
    register_handlers,
)
from src.script.common.enums import CommandType, EntityType
from src.script.entity._entity import StorableEntity
from src.script.input.input import Input
from src.script.registry._base import Registry


@register_handlers(
    {
        'input_method_name': 'get_publish_inputs',
        'handler_method_name': 'handle_publish',
        'command_type': CommandType.PUBLISH,
    },
    {
        'input_method_name': 'get_stage_inputs',
        'handler_method_name': 'handle_stage',
        'command_type': CommandType.STAGE,
    },
)
class ProjectIntegration(StorableEntity):
    """
    Represents the interface between a project and an integration.
    
    This class creates a bridge between Project and Integration instances, 
    automatically detecting and binding methods and properties that require
    a Project parameter.
    """
    
    def __init__(self, registry: Registry, project_uuid: str, integration_uuid: str, **kwargs):

        super().__init__(registry, **kwargs)

        integration_registry = registry.manager.get_by_entity_type(EntityType.INTEGRATION)
        project_registry = registry.manager.get_by_entity_type(EntityType.PROJECT)

        integration = integration_registry.get_by_id(integration_uuid)
        project = project_registry.get_by_id(project_uuid)

        self._name = f"{EntityType.PROJECT_INTEGRATION.value}-{project.name}-{integration.name}-{self.uuid}"


        self._db_fields.update({
            'project_uuid': project_uuid,
            'integration_uuid': integration_uuid,
        })

        self._config_fields = getattr(integration, 'project_integration_config_fields', [])

        self._project_ref = project.ref
        self._integration_ref = integration.ref

    @classproperty
    def type(self):
        return EntityType.PROJECT_INTEGRATION

    @classproperty
    def short_name(self):
        return 'pi'
    
    @property
    def commands(self):
        return self._commands

    @commands.setter
    def commands(self,val):
        self._commands = val
    
    @property
    def project_ref(self):
        return self._project_ref
    
    @property
    def integration_ref(self):
        return self._integration_ref

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
            if integration:
                self.logger.error(f"Error setting up integration {integration.name}: {e}")
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
                


     ######                                ##
       ##                                  ##
       ##     ## ###   ######   ##   ##  ######    #####
       ##     ###  ##  ##   ##  ##   ##    ##     ##
       ##     ##   ##  ##   ##  ##   ##    ##      ####
       ##     ##   ##  ##   ##  ##  ###    ##         ##
     ######   ##   ##  ######    ### ##     ###   #####
                       ##
    
    @classmethod    
    def get_publish_inputs(cls, registry, handler_registry, **kwargs) -> Input:
        return Input(
            name="project_integration_publish",
            title="Publish Project to Integration",
            entity_type=EntityType.PROJECT_INTEGRATION,
            handler_registry=handler_registry,
            command_type=CommandType.PUBLISH,
            children=[
                # lambda project_integration: project_integration.integration.__class__.get_publish_inputs(**kwargs)        
            ]
        )
        
    @classmethod
    def get_stage_inputs(cls, registry, handler_registry, **kwargs) -> Input:
        return Input(
            name="project_integration_stage",
            title="Stage Project to Integration",
            entity_type=EntityType.PROJECT_INTEGRATION,
            handler_registry=handler_registry,
            command_type=CommandType.PUBLISH,
            children=[
                # lambda project_integration: project_integration.integration.__class__.get_stage_inputs(**kwargs)        
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
    def handle_publish(cls, project_integration, **kwargs):
        project_integration.integration.__class__.handle_publish(**kwargs)

    @classmethod
    def handle_stage(cls, project_integration, **kwargs):
        project_integration.integration.__class__.handle_stage(**kwargs)

    