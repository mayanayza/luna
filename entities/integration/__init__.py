from common.enums import ApplicationLayer, EntityType
from .capabilities import IntegrationCapabilities
from .entity import IntegrationBase
from .service import IntegrationServiceBase
from .registry import IntegrationRegistryBase
from .cli import IntegrationSubparserBase
from .. import EntityInitializer

IntegrationInitializer = EntityInitializer(entity_type=EntityType.INTEGRATION,
                                           capabilities=IntegrationCapabilities,
                                           entity_class_base=IntegrationBase,
                                           service_class_base=IntegrationServiceBase,
                                           registry_class_base=IntegrationRegistryBase,
                                           cli_class_base=IntegrationSubparserBase)

IntegrationInitializer.validate_capabilities()

layer_classes = IntegrationInitializer.create_classes()

Integration = layer_classes[ApplicationLayer.ENTITY]
IntegrationService = layer_classes[ApplicationLayer.SERVICE]
IntegrationRegistry = layer_classes[ApplicationLayer.REGISTRY]
IntegrationSubparser = layer_classes[ApplicationLayer.CLI]

# Integration = IntegrationCapabilities.create_composed_class('Integration', IntegrationBase)
# IntegrationService = IntegrationCapabilities.create_composed_class('IntegrationService', IntegrationServiceBase)
# IntegrationRegistry = IntegrationCapabilities.create_composed_class('IntegrationRegistry', IntegrationRegistryBase)
# IntegrationSubparser = IntegrationCapabilities.create_composed_class('IntegrationSubparser', IntegrationSubparserBase)
#
# # Set entity type references
# IntegrationService.entity_class = Integration
# IntegrationRegistry.entity_class = Integration
# Integration.type = IntegrationCapabilities.type
# # Validate
# errors = IntegrationCapabilities.validate_capabilities(Integration)
# if errors:
#     raise TypeError(f"Project validation failed: {errors}")
#
__all__ = ['Integration', 'IntegrationService', 'IntegrationRegistry', 'IntegrationSubparser']