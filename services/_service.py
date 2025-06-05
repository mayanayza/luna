import re
from abc import ABC
from typing import List, Any, Type, Dict

from common.interfaces import ListableInterface, CreatableInterface, DeletableInterface, RenamableInterface, UserNameableInterface, ImplementationDiscoveryInterface
from entities.base import Entity
from entities._entity import NameableEntity, CreatableFromModuleEntity, CreatableEntity
from registries._registry import NameableEntityRegistry, CreatableFromModuleEntityRegistry
from services.base import Service


# class ListableService(Service, IListable, ABC):
#     def __init__(self, registry, **kwargs):
#         super().__init__(registry, **kwargs)
#
#     def list_entities(self, sort_by: str = "name", filter_name: str = None) -> List[Any]:
#         """List entities with enhanced error logging"""
#         self.logger.debug(f"Listing entities with sort_by='{sort_by}', filter_name='{filter_name}'")
#
#         try:
#             entities = self.registry.get_all_entities()
#             self.logger.debug(f"Retrieved {len(entities)} entities from registry")
#
#             # Apply filter
#             if filter_name:
#                 original_count = len(entities)
#                 entities = [e for e in entities if filter_name.lower() in e.name.lower()]
#                 self.logger.debug(f"Filter '{filter_name}' reduced entities from {original_count} to {len(entities)}")
#
#             fields = entities[0].fields
#             if sort_by in fields:
#                 entities.sort(key=lambda e: e.fields[sort_by])
#             elif sort_by in self.__dict__ and type(self.__dict__[sort_by]) in ('str', 'int', 'float','bool','UUID'):
#                 entities.sort(key=lambda e: e[sort_by])
#             else:
#                 self.logger.warning(f"Unknown sort_by value: '{sort_by}', using default order")
#
#             self.logger.debug(f"Returning {len(entities)} sorted entities")
#             return entities
#
#         except Exception as e:
#             self.logger.error(f"Error in list_entities: {e}")
#             raise
#
#     def get_entity_details(self, entity: Type[Entity]) -> dict:
#
#         """Get detailed information about an entity"""
#         try:
#             details = {
#                 **{ k:v for (k,v) in entity.__dict__ if type(v) in ('str', 'int', 'float','bool','UUID') },
#                 'fields': entity.fields
#             }
#
#             return details
#         except Exception as e:
#             self.logger.error(f"Error in get_entity_details: {e}")
#             raise
#
# class CreatableService(Service, ICreatable, ABC):
#     def __init__(self, registry, **kwargs):
#         super().__init__(registry, **kwargs)
#
#     def _init_entity(self, **kwargs) -> CreatableEntity:
#         return self.entity_class(registry=self.registry, **kwargs)
#
#     def create(self, name: str, **kwargs) -> Any:
#         """Create and save entity. Entity agnostic; entity-specific data handled in create implementation in subclass"""
#         self.logger.info(f"Creating new {self.entity_class.__name__} with params: {kwargs}")
#
#         try:
#             # Create entity
#             self.logger.debug(f"Instantiating {self.entity_class.__name__}")
#             entity: CreatableEntity = self._init_entity(**kwargs)
#             self.logger.debug(f"Created {self.entity_type.value}: {entity}")
#
#             # Save to database
#             if hasattr(entity, 'db'):
#                 self.logger.debug(f"Saving {self.entity_type.value} to database")
#                 success = entity.db_upsert()
#                 if not success:
#                     self.logger.error(f"Database upsert failed for {self.entity_type.value} {entity.name}")
#                     raise RuntimeError(f"Failed to save {entity.name} to database")
#                 self.logger.debug("Successfully saved to database")
#             else:
#                 self.logger.warning(f"{self.entity_type.value.title()} {entity.name} has no database connection")
#
#             self.logger.info(f"Successfully created {self.entity_type}: {entity.name}")
#             return entity
#
#         except Exception as e:
#             self.logger.error(f"Failed to create {self.entity_type}: {e}")
#             raise
#
# class DeletableService(Service, IDeletable, ABC):
#
#     def _delete(self, entity: Type[Entity]):
#         # Entity-specific delete logic, Called below in delete method
#         pass
#
#     def delete(self, entity: Type[Entity]) -> bool:
#         """Delete an entity"""
#         self.logger.info(f"Attempting to delete {self.entity_type.value}: {entity.name} (ID: {entity.uuid})")
#
#         try:
#             # Entity-specific delete logic
#             self._delete(entity)
#
#             # Remove from database
#             if hasattr(entity, 'db') and hasattr(entity, 'db_id'):
#                 self.logger.debug(f"Removing {self.entity_type.value} from database (db_id: {entity.db_id})")
#
#                 with entity.db.transaction():
#                     table = getattr(entity.db.dal, self.entity_type_name)
#                     deleted_count = entity.db.dal(table.id == entity.db_id).delete()
#                     self.logger.debug(f"Database delete affected {deleted_count} rows")
#             else:
#                 self.logger.warning(f"Entity {entity.name} has no database connection or db_id")
#
#             # Remove from registry
#             self.logger.debug(f"Unregistering {self.entity_type.value} from registry")
#             self.registry.unregister_entity(entity)
#
#             self.logger.info(f"Successfully deleted {self.entity_class.__name__}: {entity.name}")
#             return True
#
#         except Exception as e:
#             self.logger.error(f"Failed to delete {self.entity_type.value} {entity.name}: {e}")
#             raise RuntimeError(f"Failed to delete {entity.name}: {e}")

# class NameableEntityService(Service, INameable, ABC):
#     def __init__(self, registry: NameableEntityRegistry, **kwargs):
#         super().__init__(registry, **kwargs)

    # def _rename(self, entity: NameableEntity, old_name: str, old_emoji: str):
    #     # Entity-specific rename logic, Called below in rename method
    #     pass

    # def create(self, name, **kwargs) -> Any:
    #     if not NameableEntityService._is_valid_name(name):
    #         raise
    #
    #     super().create(name, **kwargs)

# class RenamableService(Service, IRenamable, ABC):
#
#     def rename(self, entity: NameableEntity, new_name: str, **kwargs) -> Dict[str, str]:
#         """Renames an entity and calls entity-specific rename function with rollback protection"""
#         # Validate new name
#         if not NameableEntityService._is_valid_name(new_name):
#             raise
#
#         # Validate emoji if provided
#         if 'emoji' in kwargs and not self._is_emoji(kwargs['emoji']):
#             raise ValueError("Invalid emoji provided")
#
#         old_name = entity.name
#         old_emoji = entity.emoji
#
#         try:
#             # Update entity
#             entity.name = new_name
#             entity.emoji = new_emoji
#
#             # Update registry index
#             self.registry.update_name_index(entity, old_name)
#
#             # Call entity-specific rename method
#             self._rename(entity, old_name, old_emoji)
#
#             # Save to database
#             entity.db_upsert()
#
#             self.logger.info(f"Renamed {self.entity_type.value}: {old_name} → {new_name}")
#             return {
#                 "old_name": old_name,
#                 "new_name": new_name,
#                 "old_emoji": old_emoji,
#                 "new_emoji": entity.emoji
#             }
#
#         except Exception as e:
#             # Rollback changes if something fails
#             entity.name = old_name
#             entity.emoji = old_emoji
#             self.registry.update_name_index(entity, new_name)
#             raise RuntimeError(f"Failed to rename {self.entity_type.value}: {e}")

# class CreatableFromModuleEntityService(Service, IModuleDiscoverable, ABC):
#
#     package: str = NotImplemented  # Will come from entity mixin
#
#     def __init__(self, registry: CreatableFromModuleEntityRegistry, **kwargs):
#         super().__init__(registry, **kwargs)
#
#     def is_module(self, name) -> bool:
#         return name in self.list_modules()
#
#     def list_modules(self):
#         self.registry.list_modules()
#
#     def _init_entity(self, submodule: str, **kwargs) -> Type[CreatableFromModuleEntity]:
#         return