from typing import Any, Type, List, Union, Dict

from common.interfaces import ListableInterface, CreatableInterface, DeletableInterface, RenamableInterface, \
    EditableInterface, ImplementationDiscoveryInterface
from entities.base import Entity
from entities.mixins import DatabasePropertyMixin, UserNameablePropertyMixin, ReadOnlyNamePropertyMixin
from services.base import Service
from abc import ABC


class ListableServiceMixin(ListableInterface, Service, ABC):
    """Service implementation of listable capability"""

    def list(self, sort_by: str = "name", filter_name: str = None) -> List[Any]:
        """List entities with enhanced error logging"""
        self.logger.debug(f"Listing entities with sort_by='{sort_by}', filter_name='{filter_name}'")

        try:
            entities = self.registry.get_all_entities()
            self.logger.debug(f"Retrieved {len(entities)} entities from registry")

            # Apply filter
            if filter_name:
                original_count = len(entities)
                entities = [e for e in entities if filter_name.lower() in e.name.lower()]
                self.logger.debug(f"Filter '{filter_name}' reduced entities from {original_count} to {len(entities)}")

            fields = entities[0].fields
            if sort_by in fields:
                entities.sort(key=lambda e: e.fields[sort_by])
            elif sort_by in self.__dict__ and type(self.__dict__[sort_by]) in ('str', 'int', 'float', 'bool', 'UUID'):
                entities.sort(key=lambda e: e[sort_by])
            else:
                self.logger.warning(f"Unknown sort_by value: '{sort_by}', using default order")

            self.logger.debug(f"Returning {len(entities)} sorted entities")
            return entities

        except Exception as e:
            self.logger.error(f"Error in list_entities: {e}")
            raise

    def details(self, entity) -> Dict[str, Any]:
        return {
            'name': entity.name,
            'uuid': str(entity.uuid),
            **entity.fields
        }

        # """Get detailed information about an entity"""
        # try:
        #     details = {
        #         **{k: v for (k, v) in entity.__dict__ if type(v) in ('str', 'int', 'float', 'bool', 'UUID')},
        #         'fields': entity.fields
        #     }
        #
        #     return details
        # except Exception as e:
        #     self.logger.error(f"Error in get_entity_details: {e}")
        #     raise

class CreatableServiceMixin(CreatableInterface, Service, ABC):
    """Service implementation of creatable capability"""

    def _create_cleanup(self, entity: Type[Entity]):
        # Entity-specific delete logic, Called below in create method
        pass

    def create(self, **kwargs) -> Any:
        """Create and save entity. Entity agnostic; entity-specific data handled in create implementation in subclass"""
        self.logger.info(f"Creating new {self.entity_class.__name__} with params: {kwargs}")
        entity = None
        try:
            # Create entity
            self.logger.debug(f"Instantiating {self.entity_class.__name__}")
            entity: Type[Entity, DatabasePropertyMixin] = self.entity_class(registry=self.registry, **kwargs)
            self.logger.debug(f"Created {self.entity_type.value}: {entity}")

            # Entity-specific create logic
            self.logger.debug(f"Doing {self.entity_type.value} create cleanup")
            self._create_cleanup(entity)

            # Save to database
            self.logger.debug(f"Saving {self.entity_type.value} to database")
            success = entity.db_upsert()
            if not success:
                self.logger.error(f"Database upsert failed for {self.entity_type.value} {entity.name}")
                raise RuntimeError(f"Failed to save {entity.name} to database")
            self.logger.debug("Successfully saved to database")

            self.logger.info(f"Successfully created {self.entity_type}: {entity.name}")
            return entity

        except Exception as e:
            if entity:
                self.registry.unregister_entity(entity)
            self.logger.error(f"Failed to create {self.entity_type}: {e}")
            raise

class DeletableServiceMixin(DeletableInterface, Service, ABC):
    """Service implementation of deletable capability"""

    def _delete_cleanup(self, entity: Type[Entity]):
        # Entity-specific delete logic, Called below in delete method
        pass

    def delete(self, entity: Union[Entity, UserNameablePropertyMixin, DatabasePropertyMixin, ReadOnlyNamePropertyMixin], **kwargs) -> bool:
        """Delete an entity"""
        self.logger.info(f"Attempting to delete {self.entity_type.value}: {entity.name} (ID: {entity.uuid})")

        try:
            self.logger.debug(f"Doing {self.entity_type.value} delete cleanup")
            self._delete_cleanup(entity)

            # Remove from database
            self.logger.debug(f"Removing {self.entity_type.value} from database (db_id: {entity.db_id})")
            with entity.db.transaction():
                table = getattr(entity.db.dal, self.entity_type_name)
                deleted_count = entity.db.dal(table.id == entity.db_id).delete()
                self.logger.debug(f"Database delete affected {deleted_count} rows")

            # Remove from registry
            self.logger.debug(f"Unregistering {self.entity_type.value}: {entity.name}")
            self.registry.unregister_entity(entity)

            self.logger.info(f"Successfully deleted {self.entity_class.__name__}: {entity.name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete {self.entity_type.value} {entity.name}: {e}")
            raise RuntimeError(f"Failed to delete {entity.name}: {e}")

class RenamableServiceMixin(RenamableInterface, Service, ABC):
    """Service implementation of renamable capability"""

    def _rename_cleanup(self, entity: Type[Entity], old_name:str, **kwargs):
        pass

    def rename(self, entity, new_name, **kwargs):
        """Rename an entity"""
        self.logger.info(f"Attempting to rename {self.entity_type.value}: {entity.name} (ID: {entity.uuid})")

        if hasattr(self, 'is_valid_name') and not self.is_valid_name(new_name):
            raise ValueError(f"Invalid name: {new_name}")

        old_name = entity.name
        entity.name = new_name

        # Entity-specific rename logic
        self.logger.debug(f"Doing {self.entity_type.value} rename cleanup")
        self._rename_cleanup(entity, old_name, **kwargs)

        # Save changes
        self.logger.debug(f"Updating record in DB")
        entity.db_upsert()

        # Update registry index
        self.logger.debug(f"Unregistering {self.entity_type.value}: {entity.name}")
        self.registry.update_name_index(entity, old_name)

        return {
            "old_name": old_name,
            "new_name": new_name,
        }

class EditableServiceMixin(EditableInterface, Service, ABC):
    """Service implementation of editable capability"""

    def edit(self, entity, **config_updates):
        """Edit an entity"""
        self.logger.info(f"Attempting to edit {self.entity_type.value}: {entity.name}")

        self.logger.debug(f"Updating {self.entity_type.value} {entity.name} config: {config_updates}")
        entity.config.update(config_updates)

        self.logger.debug(f"Updating record in DB")
        entity.db_upsert()

        return entity

class DiscoverableImplementationServiceMixin(ImplementationDiscoveryInterface, Service, ABC):
    """Service implementation of module discoverable capability"""

    def list_implementations(self):
        return self.registry.implementation_loader.get_implementation_filenames()

    def is_implementation(self, module_name):
        return module_name in self.registry.list_implementations()

class LoadableImplementationServiceMixin(CreatableInterface, Service, ABC):

    def create(self, **kwargs) -> Any:
        # Entities which implement ImplementationLoadableCapability are created 1:1 from the implementation file, which
        # creates the entity - so we stub the create method to prevent other CreatableInterface mixins from being loaded as well
        pass

class CreatableImplementationServiceMixin(CreatableInterface, Service, ABC):

    def create(self, **kwargs) -> Any:
        """Create and save entity using a selected implementation from a package for the class"""
        self.logger.info(f"Creating new {self.entity_class.__name__} with params: {kwargs}")

        implementation = kwargs.get('implementation', None)

        if implementation is None:
            raise RuntimeError(f"No implementation provided")

        try:
            # Create entity
            self.logger.debug(f"Instantiating {self.entity_class.__name__}")
            entity: Type[Entity, DatabasePropertyMixin] = self.registry.module_loader.load(**kwargs)
            self.logger.debug(f"Created {self.entity_type.value}: {entity}")

            # Save to database
            self.logger.debug(f"Saving {self.entity_type.value} to database")
            success = entity.db_upsert()
            if not success:
                self.logger.error(f"Database upsert failed for {self.entity_type.value} {entity.name}")
                raise RuntimeError(f"Failed to save {entity.name} to database")
            self.logger.debug("Successfully saved to database")

            self.logger.info(f"Successfully created {self.entity_type}: {entity.name}")
            return entity

        except Exception as e:
            self.logger.error(f"Failed to create {self.entity_type}: {e}")
            raise