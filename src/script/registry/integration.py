
from src.script.common.constants import EntityType
from src.script.entity.integration import Integration
from src.script.registry._registry import CreatableFromModuleEntityRegistry


class IntegrationRegistry(CreatableFromModuleEntityRegistry):
    def __init__(self, manager):
        super().__init__(EntityType.INTEGRATION, Integration, manager)

        entity_data = self.loader.get_entity_data_from_database(EntityType.INTEGRATION.value)
        
        for data in entity_data:
            self.loader.load_from_module(f'src.script.integration.{data['base_module']}', **data)
        
    @classmethod
    def handle_list_modules(cls, registry, **kwargs):
        return registry.loader.get_filenames_with_derived_entity_class('src.script.integration')

    @classmethod
    def handle_create(cls, registry, **kwargs):  
        base_module = kwargs.get('module', None)
        if base_module: 
            kwargs['base_module'] = base_module   
            integration = registry.loader.load_from_module(f'src.script.integration.{base_module}', **kwargs)
            registry.db.upsert(EntityType.INTEGRATION.value, integration[0])
            return integration[0]
        else:
            registry.logger.error("Can't create integration; no module param")