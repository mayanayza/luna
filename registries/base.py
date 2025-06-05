import logging
from abc import ABC
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Type
from uuid import UUID, uuid4

from common.enums import EntityType, ApplicationLayer
from services.base import Service

if TYPE_CHECKING:
    from entities.base import (
        Entity,
        EntityRef,
    )
    from registries._manager import RegistryManager


class Registry(ABC):
    """
    Base registry class that manages entities of a specific type.
    """

    layer = ApplicationLayer.REGISTRY

    # Provided in __init__ of entity's folder
    entity_type: EntityType
    entity_class: type
    entity_type_name: str

    service_class: Type[Service]
    
    def __init__(self, manager: 'RegistryManager'):
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self._uuid = uuid4()
        self._entities: Dict[UUID, 'Entity'] = {}
        self._manager: 'RegistryManager' = manager
        self._service: 'Service' = self.service_class(self)

        self.manager.register_registry(self)

    @property
    def service(self) -> 'Service':
        return self._service

    @property
    def uuid(self) -> UUID:
        return self._uuid

    @uuid.setter
    def uuid(self, val):
        self._uuid = val

    @property
    def manager(self) -> 'RegistryManager':
        return self._manager

    @manager.setter
    def manager(self, manager: 'RegistryManager'):
        self._manager = manager

    def register_entity(self, entity: 'Entity') -> None:
        """Register an entity with this registry."""
        self.logger.debug(f'Registering {entity}')
        self._entities[entity.uuid] = entity

    def unregister_entity(self, entity: 'Entity') -> None:
        """Remove an entity from this registry."""
        self.logger.debug(f"Unregistering entity: {entity}")
        del self._entities[entity.uuid]

    def get_by_id(self, entity_id: UUID) -> Optional['Entity']:
        """Get an entity by its ID."""
        return self._entities.get(entity_id, None)

    def get_by_ref(self, ref: 'EntityRef') -> 'Entity':
        return self._entities.get(ref.entity_id, None)
    
    def get_all_entities(self) -> List['Entity']:
        """Get all entities in this registry."""
        return list(self._entities.values())

    def find_entities(self, filter_func: Callable[['Entity'], bool]) -> List['Entity']:
        """Find entities based on a filter function."""
        return [entity for entity in self._entities.values() if filter_func(entity)]