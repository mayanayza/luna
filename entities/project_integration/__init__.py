from common.enums import ApplicationLayer, EntityType
from .capabilities import ProjectIntegrationCapabilities
from .entity import ProjectIntegrationBase
from .service import ProjectIntegrationServiceBase
from .registry import ProjectIntegrationRegistryBase
from .cli import ProjectIntegrationSubparserBase
from .. import EntityInitializer

ProjectIntegrationInitializer = EntityInitializer(entity_type=EntityType.PROJECT_INTEGRATION,
                                                  capabilities=ProjectIntegrationCapabilities,
                                                  entity_class_base=ProjectIntegrationBase,
                                                  service_class_base=ProjectIntegrationServiceBase,
                                                  registry_class_base=ProjectIntegrationRegistryBase,
                                                  cli_class_base=ProjectIntegrationSubparserBase)

ProjectIntegrationInitializer.validate_capabilities()

layer_classes = ProjectIntegrationInitializer.create_classes()

ProjectIntegration = layer_classes[ApplicationLayer.ENTITY]
ProjectIntegrationService = layer_classes[ApplicationLayer.SERVICE]
ProjectIntegrationRegistry = layer_classes[ApplicationLayer.REGISTRY]
ProjectIntegrationSubparser = layer_classes[ApplicationLayer.CLI]


#
# ProjectIntegration = ProjectIntegrationCapabilities.create_composed_class('ProjectIntegration', ProjectIntegrationBase)
# ProjectIntegrationService = ProjectIntegrationCapabilities.create_composed_class('ProjectIntegrationService', ProjectIntegrationServiceBase)
# ProjectIntegrationRegistry = ProjectIntegrationCapabilities.create_composed_class('ProjectIntegrationRegistry', ProjectIntegrationRegistryBase)
# ProjectIntegrationSubparser = ProjectIntegrationCapabilities.create_composed_class('ProjectIntegrationSubparser', ProjectIntegrationSubparserBase)
#
# # Set entity references
# ProjectIntegrationService.entity_class = ProjectIntegration
# ProjectIntegrationRegistry.entity_class = ProjectIntegration
# ProjectIntegration.type = ProjectIntegrationCapabilities.type
# # Validate
# errors = ProjectIntegrationCapabilities.validate_capabilities(ProjectIntegration)
# if errors:
#     raise TypeError(f"Project validation failed: {errors}")
#
__all__ = ['ProjectIntegration', 'ProjectIntegrationService', 'ProjectIntegrationRegistry', 'ProjectIntegrationSubparser']