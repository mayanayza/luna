from common.enums import EntityType
from common.capabilities import ListableCapability, EditableCapability, CreatableCapability, DeletableCapability, \
    EntityCapabilities, DatabaseCapability


class ProjectIntegrationCapabilities(EntityCapabilities):
    """Explicit capability declaration for ProjectIntegrations using class references"""
    capabilities = [
        ListableCapability,
        EditableCapability,
        CreatableCapability,
        DeletableCapability,
        DatabaseCapability
    ]
