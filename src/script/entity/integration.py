from abc import abstractmethod
from typing import List

from src.script.common.constants import EntityType
from src.script.common.decorators import classproperty
from src.script.entity._entity import CreatableFromModuleEntity
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
    def handle_stage(cls, entity, **kwargs):
        pass

    @classmethod
    @abstractmethod    
    def handle_edit(cls, entity, **kwargs):
        pass

    @classmethod
    @abstractmethod
    def handle_publish(cls, entity, **kwargs):
        pass

    @classmethod
    def handle_delete(cls, entity, **kwargs):
        """Delete this integration."""
        try:
            # Remove all project integrations
            pi_registry = entity.registry.manager.get_by_entity_type(EntityType.PROJECT_INTEGRATION)
            pi_registry.remove_pis_for_integration(entity.ref)
            
            # Delete from DB
            with entity.db.transaction():
                table = getattr(entity.db.dal, EntityType.INTEGRATION.value)
                entity.db.dal(table.id == entity.db_id).delete()
                
            # Unregister from registry
            entity.registry.unregister_entity(entity)
            
            entity.logger.info(f"Deleted integration {entity.name}")
            return True
        except Exception as e:
            entity.logger.error(f"Error deleting integration: {e}")
            raise
     
        return None

    