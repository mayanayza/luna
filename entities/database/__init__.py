from common.enums import ApplicationLayer, EntityType
from .capabilities import DatabaseCapabilities
from .entity import DatabaseBase
from .service import DatabaseServiceBase
from .registry import DatabaseRegistryBase
from .cli import DatabaseSubparserBase
from .. import EntityInitializer

DatabaseInitializer = EntityInitializer(entity_type=EntityType.DATABASE,
                                        capabilities=DatabaseCapabilities,
                                        entity_class_base=DatabaseBase,
                                        service_class_base=DatabaseServiceBase,
                                        registry_class_base=DatabaseRegistryBase,
                                        cli_class_base=DatabaseSubparserBase)

DatabaseInitializer.validate_capabilities()

layer_classes = DatabaseInitializer.create_classes()

Database = layer_classes[ApplicationLayer.ENTITY]
DatabaseService = layer_classes[ApplicationLayer.SERVICE]
DatabaseRegistry = layer_classes[ApplicationLayer.REGISTRY]
DatabaseSubparser = layer_classes[ApplicationLayer.CLI]

__all__ = layer_classes.keys()

# Database = DatabaseCapabilities.create_composed_class('Database', DatabaseBase)
# DatabaseService = DatabaseCapabilities.create_composed_class('DatabaseService', DatabaseServiceBase)
# DatabaseRegistry = DatabaseCapabilities.create_composed_class('DatabaseRegistry', DatabaseRegistryBase)
# DatabaseSubparser = DatabaseCapabilities.create_composed_class('DatabaseSubparser', DatabaseSubparserBase)
#
# # Set entity references
# DatabaseService.entity_class = Database
# DatabaseRegistry.entity_class = Database
# Database.type = DatabaseCapabilities.entity_type
# # Validate
# errors = DatabaseCapabilities.validate_capabilities(Database)
# if errors:
#     raise TypeError(f"Project validation failed: {errors}")
#
__all__ = ['Database', 'DatabaseService', 'DatabaseRegistry', 'DatabaseSubparser']