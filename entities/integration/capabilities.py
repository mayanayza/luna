from common.enums import EntityType
from common.capabilities import ListableCapability, DeletableCapability, \
    EditableCapability, DiscoverableImplementationCapability, RenamableCapability, EntityCapabilities, \
    DatabaseCapability, UserNameableImplementationCapability


class IntegrationCapabilities(EntityCapabilities):
    """Explicit capability declaration for Integrations using class references"""
    capabilities = [
        ListableCapability,
        DeletableCapability,
        DatabaseCapability,
        RenamableCapability,
        EditableCapability,
        UserNameableImplementationCapability,
        DiscoverableImplementationCapability,
    ]

