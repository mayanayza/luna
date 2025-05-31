
from src.script.common.enums import EntityType
from src.script.entity.integration import Integration
from src.script.registry._registry import CreatableFromModuleEntityRegistry


class IntegrationRegistry(CreatableFromModuleEntityRegistry):
    def __init__(self, manager):
        super().__init__(EntityType.INTEGRATION, Integration, manager)

        entity_data = self.database_loader.fetch_raw_data(EntityType.INTEGRATION.value)
        
        for data in entity_data:
            self.module_loader.load(f'src.script.integration.{data['base_module']}', **data)
        
    @classmethod
    def handle_list_modules(cls, registry, **kwargs):
        return registry.module_loader.get_module_filenames('src.script.integration')

    @classmethod
    def handle_create(cls, registry, **kwargs):  
        base_module = kwargs.get('module', None)
        if base_module: 
            kwargs['base_module'] = base_module   
            integration = registry.module_loader.load(f'src.script.integration.{base_module}', **kwargs)
            registry.db.upsert(EntityType.INTEGRATION.value, integration[0])
            return integration[0]
        else:
            registry.logger.error("Can't create integration; no module param")