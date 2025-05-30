from abc import abstractmethod
from typing import List

from src.script.common.decorators import classproperty, entity_quantity
from src.script.entity._entity import CreatableFromModuleEntity, EntityType
from src.script.entity._enum import EntityQuantity
from src.script.entity.project import Project
from src.script.input.input import Input
from src.script.templates.processor import TemplateProcessor


class Integration(CreatableFromModuleEntity):
    def __init__(self, registry, **kwargs):
        super().__init__(registry, **kwargs)
        
        self._base_module = kwargs.get('base_module')

        self._db_fields.update({
            'base_module': self._base_module
        })

        self._project_integration_config_fields: List = []
        
        # Set up templates
        self.tp = TemplateProcessor()
        
        # Initialize environment and API config for integration
        # self._init_env_vars()
        # self._init_apis()
        
    @classproperty
    def type(self):
        return EntityType.INTEGRATION

    @classproperty
    def short_name(self):
        return 'i'

    @abstractmethod
    def setup(self, project: Project, **kwargs):
        pass

    @abstractmethod
    def remove(self, project: Project, **kwargs):
        pass

    @abstractmethod
    def rename(self, project: Project, **kwargs):
        pass

     ######                                ##
       ##                                  ##
       ##     ## ###   ######   ##   ##  ######    #####
       ##     ###  ##  ##   ##  ##   ##    ##     ##
       ##     ##   ##  ##   ##  ##   ##    ##      ####
       ##     ##   ##  ##   ##  ##  ###    ##         ##
     ######   ##   ##  ######    ### ##     ###   #####
                       ##
    @classmethod
    @abstractmethod
    def get_publish_inputs(cls, entity, handler_registry, registry, **kwargs):
        pass

    @classmethod
    @abstractmethod
    def get_stage_inputs(cls, entity, handler_registry, registry, **kwargs) -> Input:
        pass


     ##   ##                         ##   ###
     ##   ##                         ##    ##
     ##   ##   ######  ## ###    ######    ##      #####   ## ###    #####
     #######  ##   ##  ###  ##  ##   ##    ##     ##   ##  ###      ##
     ##   ##  ##   ##  ##   ##  ##   ##    ##     #######  ##        ####
     ##   ##  ##  ###  ##   ##  ##   ##    ##     ##       ##           ##
     ##   ##   ### ##  ##   ##   ######   ####     #####   ##       #####

    
    @classmethod
    @abstractmethod
    def handle_stage(cls, integration, **kwargs):
        pass

    @classmethod
    @abstractmethod    
    def handle_edit(cls, integration, **kwargs):
        pass

    @classmethod
    @abstractmethod
    def handle_publish(cls, integration, **kwargs):
        pass

    @classmethod
    @entity_quantity(EntityQuantity.SINGLE)
    def handle_delete(cls, integration, **kwargs):
        """Delete this integration."""
        try:
            # Remove all project integrations
            pi_registry = integration.registry.manager.get_by_entity_type(EntityType.PROJECT_INTEGRATION)
            pi_registry.remove_pis_for_integration(integration.ref)
            
            # Delete from DB
            with integration.db.transaction():
                table = getattr(integration.db.dal, EntityType.INTEGRATION.value)
                integration.db.dal(table.id == integration.db_id).delete()
                
            # Unregister from registry
            integration.registry.unregister_entity(integration)
            
            integration.logger.info(f"Deleted integration {integration.name}")
            return True
        except Exception as e:
            integration.logger.error(f"Error deleting integration: {e}")
            raise
     
        return None

    