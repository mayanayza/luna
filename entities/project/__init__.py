from common.enums import ApplicationLayer, EntityType
from .capabilities import ProjectCapabilities
from .entity import ProjectBase
from .service import ProjectServiceBase
from .registry import ProjectRegistryBase
from .cli import ProjectSubparserBase
from .. import EntityInitializer

ProjectInitializer = EntityInitializer(entity_type=EntityType.PROJECT,
                                       capabilities=ProjectCapabilities,
                                       entity_class_base=ProjectBase,
                                       service_class_base=ProjectServiceBase,
                                       registry_class_base=ProjectRegistryBase,
                                       cli_class_base=ProjectSubparserBase)

ProjectInitializer.validate_capabilities()

layer_classes = ProjectInitializer.create_classes()

Project = layer_classes[ApplicationLayer.ENTITY]
ProjectService = layer_classes[ApplicationLayer.SERVICE]
ProjectRegistry = layer_classes[ApplicationLayer.REGISTRY]
ProjectSubparser = layer_classes[ApplicationLayer.CLI]

# Project = ProjectCapabilities.create_composed_class('Project', ProjectBase)
# ProjectService = ProjectCapabilities.create_composed_class('ProjectService', ProjectServiceBase)
# ProjectRegistry = ProjectCapabilities.create_composed_class('ProjectRegistry', ProjectRegistryBase)
# ProjectSubparser = ProjectCapabilities.create_composed_class('ProjectSubparser', ProjectSubparserBase)
#
# # Set entity references
# ProjectService.entity_class = Project
# ProjectRegistry.entity_class = Project
# Project.type = ProjectCapabilities.type
# # Validate
# errors = ProjectCapabilities.validate_capabilities(Project)
# if errors:
#     raise TypeError(f"Project validation failed: {errors}")
#
__all__ = ['Project', 'ProjectService', 'ProjectRegistry', 'ProjectSubparser']