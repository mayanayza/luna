from abc import ABC
from typing import Optional, List

from entities.base import Entity
from registries._loader import RegistryLoaderFactory
from registries.base import Registry


class NameIndexedRegistryMixin(Registry, ABC):
    """Adds name-based entity lookup"""

    def __init__(self, manager):
        self._entities_by_name = {}
        super().__init__(manager)

    def register_entity(self, entity: 'Entity'):
        """Register an entity with a name."""
        super().register_entity(entity)
        self._entities_by_name[entity.name] = entity

    def unregister_entity(self, entity):
        super().unregister_entity(entity)
        del self._entities_by_name[entity.name]

    def get_by_name(self, name: str) -> Optional['Entity']:
        return self._entities_by_name.get(name, None)

    def get_all_entities_names(self) -> List[str]:
        return list(self._entities_by_name.keys())

    def update_name_index(self, entity, old_name):
        """Update name index when entity name changes"""
        if old_name in self._entities_by_name:
            del self._entities_by_name[old_name]
        if hasattr(entity, 'name'):
            self._entities_by_name[entity.name] = entity

class DatabaseRegistryMixin(Registry, ABC):
    """Adds database connection and autoloading"""

    def __init__(self, manager):
        self._db_ref = manager.db_ref
        super().__init__(manager)
        self.database_loader = RegistryLoaderFactory.create_database_loader(self)
        self.database_loader.load()

    @property
    def db(self):
        if not hasattr(self, '_db_ref') or self._db_ref is None:
            raise RuntimeError(f"Database reference not set for {self.__class__.__name__}")
        else:
            return self.manager.get_entity_by_ref(self._db_ref)

    @db.setter
    def db(self, db_ref):
        self._db_ref = db_ref

        for entity in self._entities.values():
            entity.db = db_ref

    def register_entity(self, entity):
        super().register_entity(entity)
        entity.db = self._db_ref


class DiscoverableImplementationRegistryMixin(Registry, ABC):
    """Adds implementation discovery capabilities"""

    def __init__(self, manager):
        super().__init__(manager)
        self.implementation_loader = RegistryLoaderFactory.create_implementation_loader(self)

class LoadableImplementationRegistryMixin(Registry, ABC):
    """Creates entities from discovered implementation files"""
    def __init__(self, manager):
        super().__init__(manager)
        self.implementation_loader = RegistryLoaderFactory.create_implementation_loader(self)
        self.implementation_loader.load()

class UserNameableImplementationRegistryMixin(Registry, ABC):
    """Creates entities from discovered implementation files"""
    def __init__(self, manager):
        super().__init__(manager)
        self.implementation_loader = RegistryLoaderFactory.create_implementation_loader(self)
        self.database_loader = RegistryLoaderFactory.create_database_loader(self)

        entity_data = self.database_loader._fetch_entity_data()
        for data in entity_data:
            self.implementation_loader.load(submodule=data['module_name'], **data)

class ProjectIntegrationIndexRegistryMixin(Registry, ABC):
    """Specialized indexing for project-integration relationships"""

    def __init__(self, manager):
        self._pi_by_project = {}
        self._pi_by_integration = {}
        super().__init__(manager)

    def register_entity(self, pi):
        super().register_entity(pi)
        project_uuid, integration_uuid = pi.project_uuid, pi.integration_uuid

        if project_uuid not in self._pi_by_project:
            self._pi_by_project[project_uuid] = {}
        if integration_uuid not in self._pi_by_integration:
            self._pi_by_integration[integration_uuid] = {}

        self._pi_by_project[project_uuid][integration_uuid] = pi
        self._pi_by_integration[integration_uuid][project_uuid] = pi

    def unregister_entity(self, pi):
        super().unregister_entity(pi)
        project_uuid, integration_uuid = pi.project_uuid, pi.integration_uuid

        if project_uuid in self._pi_by_project and integration_uuid in self._pi_by_project[project_uuid]:
            del self._pi_by_project[project_uuid][integration_uuid]
        if integration_uuid in self._pi_by_integration and project_uuid in self._pi_by_integration[integration_uuid]:
            del self._pi_by_integration[integration_uuid][project_uuid]

    def get_by_project_uuid(self, project_uuid):
        return self._pi_by_project.get(project_uuid, {})

    def get_by_integration_uuid(self, integration_uuid):
        return self._pi_by_integration.get(integration_uuid, {})

    def get_pi_by_ids(self, project_uuid, integration_uuid):
        return self._pi_by_project.get(project_uuid, {}).get(integration_uuid, None)