from src.script.constants import EntityType
from src.script.entity._integration import Integration
from src.script.registry._base import CommandableRegistry


class IntegrationRegistry(CommandableRegistry):
    def __init__(self):
        super().__init__(EntityType.INTEGRATION, Integration)

    def load(self):
        """Load integration modules and data."""
        entity_data = self.loader.get_entity_data_from_database(EntityType.INTEGRATION)
        
        for data in entity_data:
            self.loader.load_from_module(f'src.script.integration.{data['integration_type']}', **data)

    def handle_list_types(self):
        pass

    def handle_create(self, **kwargs):  
        integration_type = kwargs.get('integration_type', None)
        if integration_type:      
            integration = self.loader.load_from_module(f'src.script.integration.{integration_type}', **kwargs)
            self.db.upsert(EntityType.INTEGRATION, integration[0])
            return integration[0]
        else:
            self.logger.error("Can't create integration; missing integration_type param")

    def get_integration_filenames(self):
        return self.loader.get_filenames_with_derived_entity_class('src.script.integration')