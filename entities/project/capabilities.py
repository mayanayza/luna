from common.capabilities import ListableCapability, DeletableCapability, \
    EditableCapability, RenamableCapability, NameableCapability, EntityCapabilities, DatabaseCapability
from common.enums import EntityType


class ProjectCapabilities(EntityCapabilities):
    """Explicit capability declaration for Projects using class references"""
    capabilities = [
        ListableCapability,
        NameableCapability,
        DatabaseCapability,
        DeletableCapability,
        RenamableCapability,
        EditableCapability,
    ]