from src.script.constants import EntityType
from src.script.entity._integration import Integration
from src.script.registry._base import CommandableRegistry


class IntegrationRegistry(CommandableRegistry):
    def __init__(self):
        super().__init__(EntityType.INTEGRATION, Integration)

    def load(self):
        """Load integration modules and data."""
        self.loader.load_from_database(EntityType.INTEGRATION)

    def handle_list_types(self):
        pass

    def handle_create(self, type, **kwargs):        
        integration = self.loader.load_from_module(f'src.script.integration.{type}', **kwargs)
        self.db.upsert(EntityType.INTEGRATION, integration[0])
        return integration[0]

    def get_integration_filenames(self):
        return self.loader.get_filenames_with_derived_entity_class('src.script.integration')