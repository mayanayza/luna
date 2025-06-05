from common.enums import EntityType
from common.capabilities import ListableCapability, DiscoverableImplementationCapability, EntityCapabilities, \
    LoadableImplementationCapability


class DatabaseCapabilities(EntityCapabilities):
    """Explicit capability declaration for Databases using class references"""
    capabilities = [
        ListableCapability,
        DiscoverableImplementationCapability,
        LoadableImplementationCapability
    ]

